from typing import List

from .grammar_properties import PartsOfSpeech, Cases


class MetaAttributes:
    def __getattr__(self, item):
        attr_value = self.__dict__.get(item)

        return attr_value


class GrammarForm(MetaAttributes):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __str__(self):
        return str(self.__dict__)


class Lemma(MetaAttributes):
    """
    Instances of this class should be built using LemmaBuilder class.
    """

    def __init__(self, **kwargs):
        self.text = None
        self.lexical_form = None
        self.grammar_forms = None

        self.__dict__ = kwargs

    def __str__(self):
        return "%s(%s)" % (self.text, self.lexical_form)

    def __eq__(self, other):
        return self.lexical_form == other.lexical_form

    def get_full_info(self):
        full_info = self.__dict__
        if self.grammar_forms:
            full_info['grammar_forms'] = [str(f) for f in self.grammar_forms]

        return full_info

    def belongs(self, other):
        """
        Identifies whether this lemma is a part of the given other lemma
        :param Lemma other: the other lemma
        :return: True or False
        """
        p = PartsOfSpeech

        # check adjective and noun composition
        if self.part_of_speech == p.Adjective and other.part_of_speech == p.Noun:
            adj, noun = self, other
            for adj_form in adj.grammar_forms:
                for noun_form in noun.grammar_forms:
                    if noun_form.case == adj_form.case:
                        return True

        # check noun and noun composition
        elif self.part_of_speech == p.Noun and other.part_of_speech == p.Noun:
            head_cases = (Cases.Accusative, Cases.Nominative)

            for g_form in other.grammar_forms:
                if g_form.case in head_cases:
                    return True

        elif self.part_of_speech == p.Adverb and other.part_of_speech == p.Verb:
            return True

        return False


# noinspection PyAttributeOutsideInit
class LemmaBuilder:
    def __init__(self, **kwargs):
        self.__dict__ = kwargs

    def add_text(self, text: str):
        self.text = text
        return self

    def add_lexical_form(self, lexical_form: str):
        self.lexical_form = lexical_form
        return self

    def add_part_of_speech(self, part_of_speech: str):
        self.part_of_speech = part_of_speech
        return self

    def add_params(self, **params):
        for key, item in params.items():
            self.__dict__[key] = item

    def add_grammar_form(self, grammar_form: GrammarForm):
        if self.grammar_forms:
            self.grammar_forms.append(grammar_form)
        else:
            self.grammar_forms = [grammar_form]

        return self

    def __getattr__(self, item):
        attr_value = self.__dict__.get(item)
        return attr_value

    def build(self):
        # check if the lemma was correctly built
        self._check_lemma_properties()

        return Lemma(**self.__dict__)

    def _check_lemma_properties(self):
        # lemma must contain text and lexical form
        if not self.text or not self.lexical_form or not self.part_of_speech:
            raise ValueError('Error building lemma: text, lexical form and part of speech must be specified')

        # check speech part
        if not PartsOfSpeech.contains_property(self.part_of_speech):
            raise ValueError('Error building lemma: %s is not valid part of speech' % self.part_of_speech)


class Sentence(list):
    def __init__(self):
        super(Sentence, self).__init__()

    def get_tokens(self) -> List[str]:
        return [lemma.lexical_form for lemma in self]

    def get_words_info(self):
        return [lemma.get_full_info() for lemma in self]
