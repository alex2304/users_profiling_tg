import os
from typing import List, Any, Iterable

from sklearn.externals import joblib
from sklearn.linear_model import Ridge, Lasso

from models import UserClass, Prediction
from models import UserFeatures


class Predictor:
    _clf_dump_filename = 'model_dump/classifier'
    _sel_dump_filename = 'model_dump/selector'

    def _debug(self, _msg):
        if self.debug:
            print(_msg)

    def __init__(self, classifier=None, selector=None, clustering=None, debug=False):
        self.debug = debug

        # for correct converting results of embedded methods
        if isinstance(classifier, (Ridge, Lasso)):
            self.embedded = True
            self.selector = None

        else:
            self.embedded = False
            self.selector = selector

        self.classifier = classifier
        self.clustering = clustering

    def study_model(self, known_features: List[UserFeatures],
                    from_file: bool=False, save_to_file=False,
                    select_features=True):
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
            self._debug('Selector: %s' % type(self.selector).__name__)

            self.selector.fit(x, y)
            x = self.selector.transform(x)

            self._debug('Shape after selection: %s' % str(x.shape))

        self.classifier.fit(x, y)

        # save new model to file
        if save_to_file:
            self._save_model()

    def predict(self, features: List[UserFeatures])-> List[Prediction]:
        def _round_gender_value(_f):
            return max(min(round(_f), 1), 0)

        x = self._features_to_x(features)

        if self.selector:
            x = self.selector.transform(x)

        self._debug('Classifier: %s' % type(self.classifier).__name__)

        predicted = self.classifier.predict(x)

        return [Prediction(UserClass(features[index].user_id,
                                     (_round_gender_value(gender_value) if self.embedded else gender_value)),
                           features[index])
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

        self._debug('Clustering: %s' % type(self.clustering).__name__)

        clustered = self.clustering.fit_predict(x)

        # TODO: temporary correction of classes
        count_0, count_1 = list(clustered).count(0), list(clustered).count(1)
        inverted_classes = count_0 > count_1

        # TODO: implement predictions
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
    def _xy_to_features(x: List[List[Any]], y: List[Any]) -> List[UserFeatures]:
        return [UserFeatures(_class, _features) for _features, _class in zip(x, y)]

    def _save_model(self):
        joblib.dump(self.classifier, self._clf_dump_filename)
        self._debug('Trained model saved to %s' % self._clf_dump_filename)

        if self.selector:
            joblib.dump(self.selector, self._sel_dump_filename)
            self._debug('Trained selector saved to %s' % self._sel_dump_filename)
