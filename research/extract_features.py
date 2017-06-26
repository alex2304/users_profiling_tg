from typing import Tuple, List, Any

from sklearn.feature_selection import SelectPercentile
from sklearn.feature_selection import f_classif

from models import BaseFeatures
from data import DataUploader


class FeaturesLoader(DataUploader):
    def __init__(self):
        super(FeaturesLoader, self).__init__()

    def load_test_features(self)-> List[BaseFeatures]:
        query = self.db.query('SELECT user_id, food_category, food_item FROM food_orders;')

        return [BaseFeatures(item[-1], *item[:-1]) for item in query]


def features_list_to_xy(features: List[BaseFeatures])-> Tuple[List[List[Any]], List[Any]]:
    x, y = [], []

    for f in features:
        x.append(f.features_list())
        y.append(f.class_value())

    return x, y


def xy_to_features_list(x: List[List[Any]], y: List[Any])-> List[BaseFeatures]:
    return [BaseFeatures(_class, _features) for _features, _class in zip(x, y)]


def get_selector():
    # TODO: test different selectors and implement selectors choosing
    # VarianceThreshold(threshold=(threshold * (1 - threshold)))
    return SelectPercentile(score_func=f_classif, percentile=10)


def extract_features(old_features: List[BaseFeatures])-> List[BaseFeatures]:
    x, y = features_list_to_xy(old_features)

    selector = get_selector()

    return selector.fit_transform(x, y)
