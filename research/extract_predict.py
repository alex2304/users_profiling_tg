from typing import List, Any, Tuple

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectPercentile
from sklearn.feature_selection import VarianceThreshold
from sklearn.feature_selection import f_classif

from research.features_loader import FeaturesLoader


class Classifier:
    def __init__(self, model=None):
        self.classifier = RandomForestClassifier()
        self.selector = SelectPercentile(score_func=f_classif, percentile=10)

        # threshold = .8
        # self.selector = VarianceThreshold(threshold=(threshold * (1 - threshold)))

    def study_model(self, x, y):
        self.classifier.fit(x, y)

    def extract_features(self, x: List[List[Any]], y: List[Any])-> List[Any]:
        valuable_features = self.selector.fit_transform(x, y)

        return valuable_features

    def predict(self, x: List[List[Any]])-> List[Any]:
        predicted = self.classifier.predict(x)

        return predicted


def main():
    f_loader = FeaturesLoader()
    classifier = Classifier()

    unknown = [[0, 1, 1],
                [1, 0, 0]]
    x, y = f_loader.get_test_features()

    x = classifier.extract_features(x, y)
    classifier.study_model(x, y)

    result = classifier.predict(unknown)

    print(result)


if __name__ == '__main__':
    main()
