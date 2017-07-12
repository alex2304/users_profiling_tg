import os
from typing import List, Any, Iterable

from sklearn import svm, feature_selection
from sklearn.cluster import SpectralClustering, AgglomerativeClustering, KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.externals import joblib
from sklearn.feature_selection import SelectFromModel, SelectPercentile, f_classif, VarianceThreshold, RFE, SelectFpr, \
    SelectFdr, SelectFwe
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import chi2
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from models import Prediction
from models import UserClass
from models import UserFeatures
from research.features_loading import FeaturesLoader


class Predictor:
    _clf_dump_filename = 'model_dump/classifier'
    _sel_dump_filename = 'model_dump/selector'

    def __init__(self):
        # for correct converting results of embedded methods
        self.embedded = False

        # Selectors

        # removing features with low variance
        threshold = .8
        # self.selector = VarianceThreshold(threshold=(threshold * (1 - threshold)))

        # univariate features selection
        score_func = chi2

        # remove all except specified percentile or a count with the highest score
        percentile = 10
        # self.selector = SelectPercentile(score_func=score_func, percentile=percentile)
        count = 10
        self.selector = SelectKBest(score_func=score_func, k=count)

        # select the pvalues below alpha based on different tests.
        alpha = 0.05
        # self.selector = SelectFpr(score_func=score_func, alpha=alpha)   # false positive rate test
        # self.selector = SelectFdr(score_func=score_func, alpha=alpha)   # false discovery rate test
        # self.selector = SelectFwe(score_func=score_func, alpha=alpha)   # family-wise error rate test

        # wrapped method (recursive features elimination)
        # self.selector = RFE(estimator=LinearRegression(), n_features_to_select=2)

        # Classifiers

        n_jobs = -1
        self.classifier = RandomForestClassifier(n_jobs=n_jobs)
        # self.classifier = svm.SVC(n_jobs=n_jobs)

        # Embedded methods

        alpha = 1.0
        # self.selector = None
        self.embedded = True
        self.classifier = Ridge(alpha=alpha)
        # self.classifier = Lasso(alpha=alpha)

        # Clustering
        n_clusters = 2
        self.clustering = SpectralClustering(n_clusters=n_clusters, affinity='nearest_neighbors')
        # self.clustering = AgglomerativeClustering(n_clusters=n_clusters, linkage='average')
        # self.clustering = KMeans(n_clusters=n_clusters)

    def study_model(self, known_features: List[UserFeatures]=None, from_file: bool=False, select_features=True):
        if not select_features:
            self.selector = None

        if from_file:
            if os.path.exists(self._clf_dump_filename) and \
                    (os.path.exists(self._sel_dump_filename) or not self.selector):
                self.classifier = joblib.load(self._clf_dump_filename)

                if self.selector:
                    self.selector = joblib.load(self._sel_dump_filename)

                return

            else:
                print('Warning: file %s or %s is missed. Training model from scratch...' %
                      (self._clf_dump_filename, self._sel_dump_filename))

        x, y = self._features_to_xy(known_features)

        if self.selector:
            print('Selector: %s' % type(self.selector))
            self.selector.fit(x, y)
            x = self.selector.transform(x)

            print('Shape after selection: %s' % str(x.shape))

        self.classifier.fit(x, y)

        # save new model to file
        self.save_model()

    def predict(self, features: List[UserFeatures])-> List[UserClass]:
        def _round_gender_value(_f):
            return max(min(round(_f), 1), 0)

        x = self._features_to_x(features)

        if self.selector:
            x = self.selector.transform(x)

        print('Classifier: %s' % type(self.classifier))

        predicted = self.classifier.predict(x)

        return [UserClass(features[index].user_id, (_round_gender_value(gender_value) if self.embedded else gender_value))
                for index, gender_value in enumerate(predicted)]

    def cluster(self, features: List[UserFeatures], select_features=False)-> List[UserClass]:
        def _get_corrected_gender(gender_value):
            # invert genders, if clusters are inverted
            return gender_value if not inverted_classes else abs(gender_value - 1)

        x = self._features_to_x(features)

        if select_features:
            if not self.selector:
                print('Warning: features selection required for clustering, but selector is not specified; skipped.')

            else:
                x = self.selector.transform(x)

        print('Clustering: %s' % type(self.clustering))

        clustered = self.clustering.fit_predict(x)

        # TODO: temporary correction of classes
        count_0, count_1 = list(clustered).count(0), list(clustered).count(1)
        inverted_classes = count_0 > count_1

        return [UserClass(features[index].user_id, _get_corrected_gender(gender_value))
                for index, gender_value in enumerate(clustered)]

    @staticmethod
    def _features_to_x(features: Iterable):
        return [f.features_list() for f in features]

    @staticmethod
    def _features_to_xy(features: Iterable):
        x, y = [], []

        for f in features:
            x.append(f.features_list())
            y.append(f.class_value())

        return x, y

    @staticmethod
    def xy_to_features(x: List[List[Any]], y: List[Any]) -> List[UserFeatures]:
        return [UserFeatures(_class, _features) for _features, _class in zip(x, y)]

    def save_model(self):
        joblib.dump(self.classifier, self._clf_dump_filename)
        print('Trained model saved to %s' % self._clf_dump_filename)

        if self.selector:
            joblib.dump(self.selector, self._sel_dump_filename)
            print('Trained selector saved to %s' % self._sel_dump_filename)


def predict(_type='classify', from_file=True, select_features=True):
    f_loader = FeaturesLoader()

    # update pre-classified info about known user genders
    f_loader.upload_users_genders()

    # get features of users with known and unknown genders
    known, unknown = f_loader.get_all_users_features()

    if _type == 'classify':
        print('Classifying...')
        predictions = classify(known, unknown, from_file=from_file, select_features=select_features)

    elif _type == 'cluster':
        print('Clustering...')
        predictions = cluster(known, unknown, select_features=select_features)

    else:
        raise NotImplementedError(_type)

    # save predicted genders to SQL table
    f_loader.save_predicted_genders(predictions)

    # display statistics
    correct_predictions, false_1, false_0 = 0, 0, 0
    for number, p in enumerate(predictions, 1):
        print('%d) Real: %s; Predicted: %s; RESULT: %s' % (number,
                                                           str(p.real_class()),
                                                           str(p.predicted_class()),
                                                           str(p.is_right()).upper()))
        if p.is_right():
            correct_predictions += 1
        else:
            if p.predicted_class() == 0:
                false_0 += 1
            elif p.predicted_class() == 1:
                false_1 += 1
            else:
                raise ValueError('Predicted unknown class')

    print('\n\nCorrect predictions: %d%% (%d out of %d)' % (correct_predictions * 100 / len(predictions),
                                                            correct_predictions,
                                                            len(predictions)))
    print('False predictions of 0s: %d\nFalse predictions of 1s: %d' % (false_0, false_1))


def classify(known, unknown, from_file=True, select_features=True):
    predictor = Predictor()

    # define features for studying and for prediction
    predict_count = -1000
    for_study, for_prediction = known[:predict_count], known[predict_count:]

    # study model and predict classes
    predictor.study_model(known_features=for_study, from_file=from_file, select_features=select_features)
    predicted_classes = predictor.predict(for_prediction)

    # create Prediction objects
    predictions = [Prediction(_class, features) for features, _class in zip(for_prediction, predicted_classes)]

    return predictions


def cluster(known, unknown, select_features=True):
    predictor = Predictor()

    if select_features:
        predictor.study_model(known_features=known, from_file=False, select_features=True)

    # cluster
    predicted_classes = predictor.cluster(known, select_features)

    predictions = [Prediction(_class, features) for features, _class in zip(known, predicted_classes)]

    return predictions


if __name__ == '__main__':
    predict(_type='cluster', from_file=False, select_features=True)
