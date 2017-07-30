import os
from typing import List, Any

from sklearn.externals import joblib
from sklearn.linear_model import Ridge, Lasso

from models import UserClass, UserPrediction
from models import UserSample
from models.prediction import Sample, MessagePrediction, MessageSample, Prediction


class Predictor:
    _dump_path = os.path.join(os.path.dirname(__file__), 'model_dump')

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

    def study_model(self, samples: List[Sample],
                    from_file: str=None, save_to_file: str=None,
                    select_features=True):
        if not select_features:
            self.selector = None

        if from_file:
            from_file_path = os.path.join(self._dump_path, from_file)

            classifier_path, selector_path = from_file_path + '_classifier', from_file_path + '_selector'

            if os.path.exists(classifier_path) and \
                    (os.path.exists(selector_path) or not self.selector):
                self.classifier = joblib.load(classifier_path)

                if self.selector:
                    self.selector = joblib.load(selector_path)

                return

            else:
                print('Warning: file %s or %s is missed. Training model from scratch...' %
                      (classifier_path, selector_path))

        x, y = self._samples_to_xy(samples)

        if self.selector:
            self._debug('Selector: %s' % type(self.selector).__name__)

            self.selector.fit(x, y)
            x = self.selector.transform(x)

            self._debug('Shape after selection: %s' % str(x.shape))

        self.classifier.fit(x, y)

        # save new model to file
        if save_to_file:
            to_file_path = os.path.join(self._dump_path, save_to_file)

            classifier_path, selector_path = to_file_path + '_classifier', to_file_path + '_selector'

            self._save_model(classifier_path, selector_path)

    def predict(self, samples: List[Sample])-> List[Prediction]:
        def _round_gender_value(_f):
            return max(min(round(_f), 1), 0)

        x = self._samples_to_x(samples)

        if self.selector:
            x = self.selector.transform(x)

        self._debug('Classifier: %s' % type(self.classifier).__name__)

        predicted = self.classifier.predict(x)

        predictions = []

        # matches types of samples to the corresponding types of predictions
        for sample_index, gender_value in enumerate(predicted):
            s = samples[sample_index]

            if isinstance(s, UserSample):
                prediction_type = UserPrediction

            elif isinstance(s, MessageSample):
                prediction_type = MessagePrediction

            else:
                raise NotImplementedError('Not implemented type of prediction for the type of sample: %s' %
                                          type(s).__name__)

            predictions.append(
                prediction_type(
                    UserClass(s.user_id,
                              (_round_gender_value(gender_value) if self.embedded else gender_value)),
                    s
                )
            )

        return predictions

    def cluster(self, features: List[UserSample], select_features=False)-> List[UserClass]:
        def _get_corrected_gender(gender_value):
            # invert genders, if clusters are inverted
            return gender_value if not inverted_classes else abs(gender_value - 1)

        x = self._samples_to_x(features)

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
    def _samples_to_x(features: List[Sample]):
        return [f.features_list() for f in features]

    @staticmethod
    def _samples_to_xy(samples: List[Sample]):
        x, y = [], []

        for f in samples:
            x.append(f.features_list())
            y.append(f.class_value())

        return x, y

    @staticmethod
    def _xy_to_samples(x: List[List[Any]], y: List[Any]) -> List[UserSample]:
        return [UserSample(_class, _features) for _features, _class in zip(x, y)]

    def _save_model(self, classifier_path, selector_path):
        joblib.dump(self.classifier, classifier_path)
        self._debug('Trained classifier saved to %s' % classifier_path)

        if self.selector:
            joblib.dump(self.selector, selector_path)
            self._debug('Trained selector saved to %s' % selector_path)
