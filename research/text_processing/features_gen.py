from typing import List

from copy import deepcopy
from sklearn.feature_extraction.text import CountVectorizer

from research.text_processing.mystem import TextProcessor


class TextFeaturesExtractor:
    def __init__(self, n_gram=1, max_features=1000, min_occurrence_rate=1, max_occurrence_rate=1.0, tokenizer=None):
        self.count_vectorizer = CountVectorizer(
            encoding='utf-8',
            ngram_range=(1, n_gram),
            max_df=max_occurrence_rate,
            min_df=min_occurrence_rate,
            max_features=max_features,
            tokenizer=tokenizer
        )

    def load_vocabulary(self, raw_documents: List[str], stemming=True):
        if stemming:
            with TextProcessor() as tp:
                samples_list = tp.stemming(raw_documents)

        else:
            samples_list = deepcopy(raw_documents)

        self.count_vectorizer.fit(samples_list)

    def get_features_names(self):
        return self.count_vectorizer.get_feature_names()

    def extract_features(self, samples: List[str], stemming=True):
        if stemming:
            with TextProcessor() as tp:
                samples_list = tp.stemming(samples)

        else:
            samples_list = deepcopy(samples)

        return self.count_vectorizer.transform(samples_list).toarray()
