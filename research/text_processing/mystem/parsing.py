import logging
from typing import List

from .entities import LemmaBuilder, Lemma, GrammarForm
from .grammar_properties import GrammarPropertiesParser, PartsOfSpeech, Cases, Numbers

logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s')


class LemmaParser:
    @classmethod
    def parse_lemma(cls, lemma_dict: dict) -> Lemma:
        # create lemma builder
        lb = LemmaBuilder()

        # add lemma text and lexical form
        lemma_info = lemma_dict['analysis'][0]
        lb.add_text(lemma_dict['text']).add_lexical_form(lemma_info['lex'])

        # parse grammar info
        cls._parse_grammar_info(lb, lemma_info['gr'])

        # build Lemma instance
        return lb.build()

    @classmethod
    def _parse_grammar_info(cls, lb: LemmaBuilder, grammar_info: str):
        # info parts are separated by '='
        common_info, grammar_forms = grammar_info.split('=')

        # split common information to items
        common_info = common_info.split(',')

        # read part of speech
        part_of_speech = common_info[0]
        lb.add_part_of_speech(part_of_speech)

        # split several grammar info's
        if grammar_forms.startswith('('):
            grammar_forms = cls._split_multi_grammar_forms(grammar_forms)
        else:
            grammar_forms = [grammar_forms]

        # split grammar forms
        grammar_forms = [g_form.split(',') for g_form in grammar_forms]

        # add common info (omit part of speech)
        lb.add_params(**GrammarPropertiesParser.parse_common_info(part_of_speech, common_info[1:]))

        # add grammar forms
        for g_form in grammar_forms:
            grammar_form = GrammarForm(**GrammarPropertiesParser.parse_grammar_forms(part_of_speech, g_form))
            lb.add_grammar_form(grammar_form)

    @staticmethod
    def _split_multi_grammar_forms(multi_grammar_info: str) -> List[str]:
        return multi_grammar_info[1:-1].split('|')

    @classmethod
    def get_delimiter_lemma(cls, delimiter_text: str) -> Lemma:
        # create lemma builder
        lb = LemmaBuilder()

        # add lemma text and lexical form
        lb.add_text(delimiter_text).add_lexical_form(delimiter_text).add_part_of_speech(PartsOfSpeech.Delimiter)

        # build Lemma instance
        return lb.build()

    @classmethod
    def get_arbitrary_lemma(cls, lemma_text: str) -> Lemma:
        # create lemma builder
        lb = LemmaBuilder()

        # text, lexical form, part of speech (Noun by default)
        lb.add_text(lemma_text).add_lexical_form(lemma_text).add_part_of_speech(PartsOfSpeech.Noun)

        # add grammar form (Nominative, single by default)
        g_form_values = [Numbers.Single, Cases.Nominative]
        grammar_form = GrammarForm(**GrammarPropertiesParser.parse_grammar_forms(PartsOfSpeech.Noun, g_form_values))
        lb.add_grammar_form(grammar_form)

        # build Lemma instance
        return lb.build()
