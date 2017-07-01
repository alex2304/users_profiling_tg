from typing import List, Any, Iterable

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectPercentile
from sklearn.feature_selection import f_classif

from models import UserClass
from models import UserFeatures
from research.features_loading import FeaturesLoader


class Classifier:
    def __init__(self, model=None):
        self.classifier = RandomForestClassifier()
        self.selector = SelectPercentile(score_func=f_classif, percentile=10)

        # threshold = .8
        # self.selector = VarianceThreshold(threshold=(threshold * (1 - threshold)))

    def study_model(self, features: List[UserFeatures]):
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

    # unknown = [[0, 1, 1],
    #             [1, 0, 0]]
    known, unknown = f_loader.get_all_users_features()

    # x = classifier.extract_features(x, y)
    classifier.study_model(known)

    predicted = classifier.predict(unknown)

    f_loader.save_predicted_genders({f.user_id: f.gender_letter for f in predicted})


if __name__ == '__main__':
    main()
