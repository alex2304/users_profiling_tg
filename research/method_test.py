from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold

from research.features_extraction import FeaturesExtractor
from research.performance_analysis import Experiment
from research.prediction import Predictor


def test_method(s_type='users'):
    """
    :param s_type: 'users' or 'messages'
    """
    if s_type == 'users':
        known, unknown = f_loader.get_all_users_features()

    elif s_type == 'messages':

        known, unknown = f_loader.get_messages_features(from_file=False, save_to_file=True)

    else:
        raise NotImplementedError('Unknown features type %s' % s_type)

    # define features for studying and for prediction
    predict_count = -1000
    for_study, for_prediction = known[:predict_count], known[predict_count:]

    c = RandomForestClassifier()

    threshold = 0.8
    s = VarianceThreshold(threshold=threshold * (1 - threshold))

    predictor = Predictor(c, s, debug=True)

    predictor.study_model(for_study, save_to_file='messages')

    predictions = predictor.predict(for_prediction)

    Experiment.display_classifying_result(c, s, predictions)


if __name__ == '__main__':
    f_loader = FeaturesExtractor()

    test_method(s_type='messages')
