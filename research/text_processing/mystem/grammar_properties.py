from typing import List, Type


class GrammarPropertyBase:
    p_shorthand = 'base'

    @classmethod
    def contains_property(cls, p_name):
        properties_values = cls.__dict__.values()

        return p_name in properties_values


class PartsOfSpeech(GrammarPropertyBase):
    p_shorthand = 'part_of_speech'

    Adjective = 'A'
    Noun = 'S'
    Verb = 'V'
    Proposition = 'PR'
    Pronoun = 'SPRO'
    Adverb = 'ADV'
    AdvPro = 'ADVPRO'
    AdjPro = 'APRO'
    AdjNum = 'ANUM'
    ComPart = 'COM'
    Conjunction = 'CONJ'
    Interjection = 'INTJ'
    Numeral = 'NUM'
    Particle = 'PART'
    Delimiter = 'Delimiter'
    Comma = 'Comma'


class Genders(GrammarPropertyBase):
    p_shorthand = 'gender'

    M = 'муж'
    F = 'жен'
    A = 'сред'


class Numbers(GrammarPropertyBase):
    p_shorthand = 'number'

    Single = 'ед'
    Plural = 'мн'


class Cases(GrammarPropertyBase):
    p_shorthand = 'case'

    Nominative = 'им'
    Genitive = 'род'
    Dative = 'дат'
    Accusative = 'вин'
    Instrumental = 'твор'
    Prepositional = 'пр'
    Partial = 'парт'
    Local = 'местн'
    Vocative = 'зват'


class NounsAnimate(GrammarPropertyBase):
    p_shorthand = 'noun_animate'

    Animate = 'од'
    Inanimate = 'неод'


class AdjForms(GrammarPropertyBase):
    p_shorthand = 'adj_form'

    Brief = 'кр'
    Plentiful = 'полн'
    Possessive = 'притяж'


class VerbsReprs(GrammarPropertyBase):
    p_shorthand = 'verb_repr'

    Infinitive = 'инф'
    Gerund = 'деепр'
    Participle = 'прич'
    Indicative = 'изъяв'
    Imperative = 'пов'


class VerbsTimes(GrammarPropertyBase):
    p_shorthand = 'verb_time'

    Present = 'наст'
    Permeate = 'непрош'
    Past = 'прош'


class VerbsKinds(GrammarPropertyBase):
    p_shorthand = 'verb_kind'

    Imperfect = 'несов'
    Perfect = 'сов'


class VerbsTransitivity(GrammarPropertyBase):
    p_shorthand = 'verb_transitivity'

    Transitive = 'пе'
    Intransitive = 'нп'


class VerbsVoice(GrammarPropertyBase):
    p_shorthand = 'verb_voice'

    Active = 'действ'
    Passive = 'страд'


class VerbsFaces(GrammarPropertyBase):
    p_shorthand = 'verb_face'

    First = '1-л'
    Second = '2-л'
    Third = '3-л'


class VerbsCompDegrees(GrammarPropertyBase):
    p_shorthand = 'verb_comp_degree'

    Supreme = 'прев'
    Comparative = 'срав'


class OtherProperties(GrammarPropertyBase):
    p_shorthand = 'other'

    Parenthesis = 'вводн'
    Geo = 'гео'
    Difficult = 'затр'
    Personal = 'имя'
    Distorted = 'искаж'
    MaleFemale = 'мж'
    Obscene = 'обсц'
    Patronymic = 'отч'
    Predicate = 'прдк'
    Informal = 'разг'
    Rare = 'редк'
    Abbreviation = 'сокр'
    Obsolete = 'устар'
    Surname = 'фам'


class GrammarPropertiesParser:
    @classmethod
    def parse_grammar_forms(cls, part_of_speech: str, g_form_values: List[str]) -> dict:
        """
        Identifies what the grammar form properties are specified in grammar_info.
        Builds dictionary, where keys are field names of grammar form properties.
        :param str part_of_speech: valid part of speech of some lemma
        :param List[str] g_form_values: grammar info section of some lemma
        :return: dict of grammar form properties' names, and their values

        .::note: :g_form_values - list of values from 'grammar' Mystem output section (splitted by commas)
        """
        p = PartsOfSpeech

        if not p.contains_property(part_of_speech):
            raise ValueError('Error getting grammar form values: incorrect part of speech %s ' % part_of_speech)

        g_form_properties_holders = cls._get_g_form_p_holders(part_of_speech)

        return cls._get_properties_values(g_form_values, g_form_properties_holders)

    @classmethod
    def parse_common_info(cls, part_of_speech: str, common_values: List[str]):
        """
        Identifies what the common properties are specified in common_info.
        Builds dictionary, where keys are field names of common properties.
        :param str part_of_speech: valid part of speech of some lemma
        :param List[str] common_values: common info section of some lemma
        :return: dict of common properties' names, and their values

        .::note: :common_values - list of values from 'common_info' Mystem output section (splitted by commas)
        """
        p = PartsOfSpeech

        if not p.contains_property(part_of_speech):
            raise ValueError('Error getting common values: incorrect part of speech %s ' % part_of_speech)

        common_properties_holders = cls._get_common_p_holders(part_of_speech)

        return cls._get_properties_values(common_values, common_properties_holders)

    @staticmethod
    def _get_g_form_p_holders(part_of_speech: str) -> List[Type[GrammarPropertyBase]]:
        p = PartsOfSpeech

        # holders of properties of adjectives and nouns
        if part_of_speech in (p.Adjective, p.AdjPro, p.Noun, p.Numeral, p.Pronoun):
            return [AdjForms, NounsAnimate, Genders, Numbers, Cases]

        # holders of properties of verbs and adverbs
        elif part_of_speech in (p.Verb, p.Adverb, p.AdvPro):
            return [VerbsCompDegrees, VerbsReprs, VerbsKinds, VerbsFaces, VerbsTimes, VerbsTransitivity, VerbsVoice]

        else:
            return [OtherProperties]

    @staticmethod
    def _get_common_p_holders(part_of_speech: str):
        p = PartsOfSpeech

        # adjectives
        if part_of_speech in (p.Adjective, p.AdjPro):
            return [AdjForms]

        # verbs, adverbs
        elif part_of_speech in (p.Verb, p.Adverb, p.AdvPro):
            return [VerbsCompDegrees, VerbsReprs, VerbsKinds, VerbsFaces, VerbsTimes, VerbsTransitivity, VerbsVoice]

        # nouns and related
        elif part_of_speech in (p.Noun, p.Numeral, p.Pronoun):
            return [NounsAnimate, Genders, Numbers, Cases]

        else:
            return [OtherProperties]

    @classmethod
    def _get_properties_values(cls, p_values: List[str], p_holders: List[Type[GrammarPropertyBase]]):
        result_dict = {}

        for p_value in p_values:
            for p_holder in p_holders:
                if p_holder.contains_property(p_value):
                    result_dict[p_holder.p_shorthand] = p_value

        return result_dict
