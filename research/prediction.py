from typing import List, Any

from sklearn.ensemble import RandomForestClassifier

from models import BaseFeatures
from research.extract_features import FeaturesLoader, extract_features, features_list_to_xy


def predict(features: List[BaseFeatures])-> List[Any]:
    x, y = features_list_to_xy(features)

    classifier = RandomForestClassifier()
    classifier.fit(x, y)

    predicted = classifier.predict(x)
    print(predicted)


def main():
    f_loader = FeaturesLoader()
    features = f_loader.load_test_features()
    features = extract_features(features)

    print(predict(features))


if __name__ == '__main__':
    main()
