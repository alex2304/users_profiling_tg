import os
from typing import List

from sklearn.cluster import SpectralClustering, AgglomerativeClustering, KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold, SelectPercentile, SelectKBest, SelectFpr, SelectFdr, \
    SelectFwe, RFE, f_classif
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.svm import LinearSVC, SVC
from sklearn.tree import DecisionTreeClassifier

from models import Prediction
from research.extract_predict import Predictor
from research.features_loading import FeaturesLoader


class Experiment:
    _report_file_name = 'results/report.txt'
    _report_file_path = os.path.join(os.path.dirname(__file__), _report_file_name)

    # Clustering
    n_clusters = 2
    agglomerative_linkage = 'average'
    spectral_affinity = 'nearest_neighbors'

    clustering = [
        SpectralClustering(n_clusters=n_clusters, affinity=spectral_affinity),
        AgglomerativeClustering(n_clusters=n_clusters, linkage=agglomerative_linkage),
        KMeans(n_clusters=n_clusters)
    ]

    # Selectors
    variance_threshold = .5
    score_func = f_classif
    best_percentile = 25
    best_count = 25
    tests_alpha = 0.1
    rfe_estimator = LinearRegression()
    rfe_features_number = 8

    selectors = [
        VarianceThreshold(threshold=(variance_threshold * (1 - variance_threshold))),
        SelectPercentile(score_func=score_func, percentile=best_percentile),
        SelectKBest(score_func=score_func, k=best_count),
        SelectFpr(score_func=score_func, alpha=tests_alpha),  # false positive rate test
        SelectFdr(score_func=score_func, alpha=tests_alpha),  # false discovery rate test
        SelectFwe(score_func=score_func, alpha=tests_alpha),  # family-wise error rate test
        RFE(estimator=rfe_estimator, n_features_to_select=rfe_features_number)
    ]

    # Classifiers
    n_jobs = -1

    classifiers = [
        RandomForestClassifier(n_jobs=n_jobs),
        SVC(),
        DecisionTreeClassifier(),
        LinearSVC(C=0.01, penalty="l1", dual=False)
    ]

    # Embedded

    embedded_alpha = 1
    embedded = [
        Ridge(alpha=embedded_alpha),
        Lasso(alpha=embedded_alpha)
    ]

    @classmethod
    def _get_statistic(cls, predictions: List[Prediction]):
        # display statistics
        correct_predictions, true_1, true_0, false_1, false_0 = 0, 0, 0, 0, 0
        for number, p in enumerate(predictions, 1):
            if p.is_right():
                correct_predictions += 1
                if p.predicted_class() == 0:
                    true_0 += 1
                elif p.predicted_class() == 1:
                    true_1 += 1
                else:
                    raise ValueError('Predicted unknown class %s' % str(p.predicted_class()))
            else:
                if p.predicted_class() == 0:
                    false_0 += 1
                elif p.predicted_class() == 1:
                    false_1 += 1
                else:
                    raise ValueError('Predicted unknown class %s' % str(p.predicted_class()))

        return correct_predictions, true_0, true_1, false_0, false_1

    @classmethod
    def log_classifying_result(cls, classifier, selector, predictions: List[Prediction]):
        mode = 'a' if os.path.exists(cls._report_file_path) else 'w'

        with open(cls._report_file_path, mode, encoding='utf-8') as f:
            f.write('%s %s ' % (type(classifier).__name__, type(selector).__name__))

            correct_predictions, true_0, true_1, false_0, false_1 = cls._get_statistic(predictions)

            f.write('{corr_percent}% {corr_count} {incorrect_count} {true_0} {false_0} {true_1} {false_1}\n'.format(
                corr_percent=correct_predictions * 100 / len(predictions),
                corr_count=correct_predictions,
                incorrect_count=len(predictions) - correct_predictions,
                false_0=false_0,
                true_0=true_0,
                false_1=false_1,
                true_1=true_1)
            )

    @classmethod
    def display_classifying_result(cls, classifier, selector, predictions: List[Prediction]):
        print('\n\nClassifier: %s\nSelector: %s\nResults:' % (type(classifier).__name__, type(selector).__name__))

        correct_predictions, true_0, true_1, false_0, false_1 = cls._get_statistic(predictions)

        print('{correct_percent}% {correct_count}\n{true_0} {false_1}\n{false_0} {true_1}'.format(
            correct_percent=correct_predictions * 100 / len(predictions),
            correct_count=correct_predictions,
            false_0=false_0,
            true_0=true_0,
            false_1=false_1,
            true_1=true_1))

        print('\n\n')

    @classmethod
    def start(cls):
        if os.path.exists(cls._report_file_path):
            os.remove(cls._report_file_path)


if __name__ == '__main__':
    f_loader = FeaturesLoader()

    # update pre-classified info about known user genders
    f_loader.upload_users_genders()

    # get features of users with known and unknown genders
    known, unknown = f_loader.get_all_users_features()

    # define features for studying and for prediction
    predict_count = -1000
    for_study, for_prediction = known[:predict_count], known[predict_count:]

    # prepare environment for starting
    Experiment.start()

    print('Experiment started')

    selectors = False
    classifiers = False
    embedded = True

    # classifiers with selectors
    if selectors:
        for c in Experiment.classifiers:
            for s in Experiment.selectors:
                predictor = Predictor(c, s)
                predictor.study_model(for_study)

                Experiment.log_classifying_result(c, s, predictor.predict(for_prediction))

    # classifiers without selectors
    if classifiers:
        for c in Experiment.classifiers:
            predictor = Predictor(classifier=c)
            predictor.study_model(for_study)

            Experiment.log_classifying_result(classifier=c, selector=None, predictions=predictor.predict(for_prediction))

    # embedded methods
    if embedded:
        for c in Experiment.embedded:
            predictor = Predictor(classifier=c)
            predictor.study_model(for_study)

            Experiment.log_classifying_result(classifier=c, selector=None, predictions=predictor.predict(for_prediction))
