
# test a single method
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold

from research.extract_predict import Predictor
from research.features_loading import FeaturesLoader
from research.performance_analysis import Experiment

if __name__ == '__main__':
    f_loader = FeaturesLoader()

    # get features of users with known and unknown genders
    known, unknown = f_loader.get_all_users_features()

    # define features for studying and for prediction
    predict_count = -100
    for_study, for_prediction = known[:predict_count], known[predict_count:]

    c = RandomForestClassifier()
    threshold = 0.
    s = VarianceThreshold(threshold=threshold*(1-threshold))

    predictor = Predictor(c, s, debug=True)
    predictor.study_model(for_study)

    predictions = predictor.predict(for_prediction)

    Experiment.display_classifying_result(c, s, predictions)