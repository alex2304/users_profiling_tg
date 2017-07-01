from typing import List, Any, Iterable

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectPercentile
from sklearn.feature_selection import f_classif

from data.transferring import DataUploader
from models import Prediction
from models import UserClass
from models import UserFeatures
from research.features_loading import FeaturesLoader


class Classifier:
    def __init__(self, model=None):
        self.classifier = RandomForestClassifier()
        self.selector = SelectPercentile(score_func=f_classif, percentile=10)

        # threshold = .8
        # self.selector = VarianceThreshold(threshold=(threshold * (1 - threshold)))

    def study_model(self, features: List[UserFeatures]=None, from_file: bool=None):
        x, y = self._features_to_xy(features)

        self.classifier.fit(x, y)

    def extract_features(self, x: List[List[Any]], y: List[Any])-> List[Any]:
        valuable_features = self.selector.fit_transform(x, y)

        return valuable_features

    def predict(self, features: List[UserFeatures])-> List[UserClass]:
        x = self._features_to_x(features)

        predicted = self.classifier.predict(x)

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


def main():
    f_loader = FeaturesLoader()
    classifier = Classifier()

    # update pre-classified info about known user genders
    f_loader.upload_users_genders()

    # get features of user with known and unknown genders
    known, unknown = f_loader.get_all_users_features()

    # define features for studying and for prediction
    for_study, for_prediction = known[:-5], known[-10:]

    # study model
    classifier.study_model(features=for_study)

    # predict classes and create Prediction objects
    predicted_classes = classifier.predict(for_prediction)
    predictions = [Prediction(_class, features) for features, _class in zip(for_prediction, predicted_classes)]

    # save predicted genders to SQL table
    f_loader.save_predicted_genders(predictions)

    # display statistics
    correct_predictions = 0
    for number, p in enumerate(predictions, 1):
        print('%d) Real: %s; Predicted: %s; RESULT: %s' % (number,
                                                           str(p.real_class()),
                                                           str(p.predicted_class()),
                                                           str(p.is_right()).upper()))
        if p.is_right():
            correct_predictions += 1

    print('\n\nCorrect predictions: %d%% (%d out of %d)' % (correct_predictions * 100 / len(predictions),
                                                            correct_predictions,
                                                            len(predictions)))

if __name__ == '__main__':
    main()
