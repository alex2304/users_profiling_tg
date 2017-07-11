import os
from typing import List, Any, Iterable

from sklearn import svm, feature_selection
from sklearn.ensemble import RandomForestClassifier
from sklearn.externals import joblib
from sklearn.feature_selection import SelectFromModel, SelectPercentile, f_classif, VarianceThreshold, RFE
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import chi2
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from models import Prediction
from models import UserClass
from models import UserFeatures
from research.features_loading import FeaturesLoader


class Classifier:
    _clf_dump_filename = 'model_dump/classifier'
    _sel_dump_filename = 'model_dump/selector'

    def __init__(self, model=None):
        # classifiers
        self.classifier = RandomForestClassifier(n_jobs=2)
        # self.classifier = svm.SVC()

        # selectors
        # threshold = .8
        # self.selector = VarianceThreshold(threshold=(threshold * (1 - threshold)))
        self.selector = RFE(estimator=LinearRegression(), n_features_to_select=10)
        # self.selector = SelectPercentile(score_func=f_classif, percentile=10)
        # self.selector = SelectKBest(score_func=chi2, k=10)

    def study_model(self, features: List[UserFeatures]=None, from_file: bool=False):
        if from_file:
            if os.path.exists(self._clf_dump_filename) and os.path.exists(self._sel_dump_filename):
                self.classifier = joblib.load(self._clf_dump_filename)
                self.selector = joblib.load(self._sel_dump_filename)
                return

            else:
                print('Warning: file %s or %s is missed. Training model from scratch...' %
                      (self._clf_dump_filename, self._sel_dump_filename))

        x, y = self._features_to_xy(features)

        self.selector.fit(x, y)

        x = self.selector.transform(x)

        self.classifier.fit(x, y)

        # save new model to file
        self.save_model()

    def predict(self, features: List[UserFeatures])-> List[UserClass]:
        x = self._features_to_x(features)

        useful_features = self.selector.transform(x)

        predicted = self.classifier.predict(useful_features)

        return [UserClass(features[index].user_id, gender_value)
                for index, gender_value in enumerate(predicted)]

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
        joblib.dump(self.selector, self._sel_dump_filename)

        print('Trained model saved to %s' % self._clf_dump_filename)
        print('Trained selector saved to %s' % self._sel_dump_filename)


def main():
    f_loader = FeaturesLoader()

    # update pre-classified info about known user genders
    f_loader.upload_users_genders()

    classifier = Classifier()

    # get features of users with known and unknown genders
    known, unknown = f_loader.get_all_users_features()

    # define features for studying and for prediction
    predict_count = -1000
    for_study, for_prediction = known[:predict_count], known[predict_count:]
    # for_prediction = unknown

    # study model
    classifier.study_model(features=for_study, from_file=False)

    # predict classes and create Prediction objects
    predicted_classes = classifier.predict(for_prediction)
    predictions = [Prediction(_class, features) for features, _class in zip(for_prediction, predicted_classes)]

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
                raise NotImplementedError()

    print('\n\nCorrect predictions: %d%% (%d out of %d)' % (correct_predictions * 100 / len(predictions),
                                                            correct_predictions,
                                                            len(predictions)))

    print('False predictions of 0s: %d\nFalse predictions of 1s: %d' % (false_0, false_1))

if __name__ == '__main__':
    main()
