import re
import traceback
from itertools import product
from typing import List, Union

from pyaspeller import YandexSpeller

from .entities import Sentence
from .framework import Mystem
from .parsing import LemmaParser


class TextProcessor(Mystem):
    """
    Should be used in conjunction with 'with' context management operator
    """
    _lemma_pattern = re.compile('.*[а-яА-Яa-zA-Z]+.*')

    text_groups_delimiter = '|'

    def __init__(self):
        super().__init__()
        self._speller = YandexSpeller()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            print('%s\nLanguageProcessor closed forcibly: "%s": "%s"' % (str(exc_tb), str(exc_type), str(exc_val)))

        self.close()

    @classmethod
    def _preprocess_text(cls, _text: str) -> str:
        """
        Replace all 'ё' with 'е'
        """
        return _text.lower().replace('ё', 'е')

    def get_spelling_variants(self, text: str) -> List[str]:
        """
        Returns list of all possible text spellings
        """
        text_words = text.split(' ')

        # get pairs of {source word: [variants of correction]}
        corrections = {w_info.get('word'): w_info.get('s')
                       for w_info in self._speller.spell(text)}

        # fill array like [['Мама'], ['мыла', 'мыло'], ['раму', 'рамп]]
        words_variants = []
        for word in text_words:
            word_spellings = [word]

            if corrections.get(word):
                word_spellings.extend(corrections.get(word))

            words_variants.append(word_spellings)

        # iterate through text products and create text variants
        text_variants = [' '.join(words_product)
                         for words_product in product(*words_variants)]

        return text_variants

    def stemming(self, text: Union[str, List[str]], validate_lemmas=False) -> Union[str, List[str]]:
        """
        Performs stemming on given text(s).
        Returns string of tokens in the original order for each given text.

        :param validate_lemmas: if True, only lemmas which match the pattern will be added
        :param text: if list of texts is passed - they are grouped by delimiter and are processed at once
        """
        if text is None:
            return []

        if isinstance(text, list):
            _text = (' %s ' % self.text_groups_delimiter).join(text)

        else:
            _text = text

        _text = self._preprocess_text(_text)

        analyzed = self.analyze(_text)

        sentence = self._build_sentence(analyzed, validate_lemmas=validate_lemmas)

        tokens = sentence.get_tokens()

        # if there were list of texts
        if isinstance(text, list):
            tokens_string = ' '.join(tokens)

            return [t.strip()
                    for t in tokens_string.split(self.text_groups_delimiter)]

        else:
            return ' '.join(tokens)

    @classmethod
    def _build_sentence(cls, analyzed: dict, validate_lemmas) -> Sentence:
        sentence = Sentence()

        for l_dict in analyzed:
            analysis = l_dict.get('analysis')

            # only words which have 'analyzed' section, and not a 'bastard', are really recognized lemmas
            if analysis and analysis[-1].get('qual') != 'bastard':
                try:
                    lemma = LemmaParser.parse_lemma(l_dict)
                    sentence.append(lemma)

                except Exception as e:
                    print('%s: %s' % (str(type(e)), str(e)))
                    traceback.print_tb(e.__traceback__)

            # groups delimiter
            elif cls.text_groups_delimiter in l_dict.get('text'):
                sentence.append(LemmaParser.get_delimiter_lemma(cls.text_groups_delimiter))

            # not-recognized word
            else:
                if validate_lemmas and re.match(cls._lemma_pattern, l_dict.get('text')) or not validate_lemmas:
                    if l_dict.get('text') != ' ':
                        sentence.append(LemmaParser.get_arbitrary_lemma(l_dict.get('text')))

        return sentence
