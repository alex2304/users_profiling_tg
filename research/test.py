from sklearn import datasets
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectFromModel
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import SelectPercentile
from sklearn.feature_selection import VarianceThreshold
from sklearn.feature_selection import chi2
import numpy as np
import matplotlib.pyplot as plt
from sklearn.feature_selection import f_classif
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

if __name__ == '__main__':
    X = [[0, 0, 1],
         [0, 1, 0],
         [1, 0, 0],
         [0, 1, 1],
         [0, 1, 0],
         [0, 1, 1]]
    Y = [0, 1, 0, 1, 1, 1]

    to_predict = [
        [0, 0],
        [0, 1],
        [1, 0],
        [1, 1],
        [0, 0],
        [0, 1],
        [1, 0],
        [1, 1],
    ]

    threshold = .8
    select = VarianceThreshold(threshold=(threshold * (1 - threshold)))
    X = select.fit_transform(X, Y)
    print(X)

    classifier = RandomForestClassifier()
    classifier.fit(X, Y)

    predicted = classifier.predict(to_predict)
    print(predicted)
    exit(0)

    # The iris dataset
    iris = datasets.load_iris()

    # Some noisy data not correlated
    E = np.random.uniform(0, 0.1, size=(len(iris.data), 20))

    # Add the noisy data to the informative features
    X = np.hstack((iris.data, E))
    y = iris.target
    plt.figure(1)
    plt.clf()

    X_indices = np.arange(X.shape[-1])

    selector = SelectPercentile(f_classif, percentile=10)
    selector.fit(X, y)
    scores = -np.log10(selector.pvalues_)
    scores /= scores.max()
    plt.bar(X_indices - .45, scores, width=.2,
            label=r'Univariate score ($-Log(p_{value})$)', color='darkorange')

    plt.show()
    exit(0)

    clf = Pipeline([
        ('feature_selection', SelectPercentile(f_classif, percentile=10)),
        ('classification', RandomForestClassifier())
    ])
    classified = clf.fit(X, y)
