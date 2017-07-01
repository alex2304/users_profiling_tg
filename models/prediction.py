import functools


class UserFeatures:
    def __init__(self, user_id, _class, *features):
        self.user_id = user_id

        self._features = []
        self._class = _class

        for f in features:
            if isinstance(f, list) or isinstance(f, tuple):
                self._features.extend(f)

            else:
                self._features.append(f)

    def features_list(self):
        return self._features

    def class_value(self):
        return self._class

    def set_class(self, _class):
        self._class = _class


@functools.total_ordering
class Features:
    def __init__(self, *features):
        self.features = features

    def __cmp__(self, other):
        """
        1) Chat > Bot
        2) If chats: compare chat_id
        3) If bots: compare bot_title
        """
        if isinstance(self, FeaturesFromChat):
            if isinstance(other, FeaturesFromChat):
                return 1 if self.chat_id > other.chat_id else -1

            elif isinstance(other, FeaturesFromBot):
                return 1

        elif isinstance(self, FeaturesFromBot):
            if isinstance(other, FeaturesFromBot):
                return 1 if self.bot_title > other.bot_title else -1

            elif isinstance(other, FeaturesFromChat):
                return 0

    def to_values_list(self):
        return self.features

    def __eq__(self, other):
        if isinstance(self, FeaturesFromChat) and isinstance(other, FeaturesFromChat):
            return self.chat_id == other.chat_id

        elif isinstance(self, FeaturesFromBot) and isinstance(other, FeaturesFromBot):
            return self.bot_title == other.bot_title

    def __gt__(self, other):
        if isinstance(self, FeaturesFromChat):
            if isinstance(other, FeaturesFromChat):
                return self.chat_id > other.chat_id

            elif isinstance(other, FeaturesFromBot):
                return True

        elif isinstance(self, FeaturesFromBot):
            if isinstance(other, FeaturesFromBot):
                return self.bot_title > other.bot_title

            elif isinstance(other, FeaturesFromChat):
                return False


class FeaturesFromChat(Features):
    def __cmp__(self, other):
        pass

    def __init__(self, chat_id, participation, freq=-1, length=-1, diff=-1):
        super().__init__(participation, freq, length, diff)

        self.chat_id = chat_id

    def __hash__(self):
        return self.chat_id


class FeaturesFromBot(Features):
    _languages = {
        'ru': 0,
        'en': 1
    }

    def __init__(self, bot_title, participation, language=None):
        super().__init__(participation, self._languages.get(language or 'ru'))

        self.bot_title = bot_title

    def __hash__(self):
        return hash(self.bot_title)


class UserClass:
    _genders = {
        'f': 0,
        'm': 1,
        'u': -1
    }

    def _resolve_letter(self, gender_value):
        for k, v in self._genders.items():
            if gender_value == v:
                return k

        return 'u'

    def __init__(self, user_id, gender):
        self.user_id = user_id

        if not isinstance(gender, str):
            self.gender_letter = self._resolve_letter(gender)

        else:
            self.gender_letter = gender

    def gender_value(self):
        return self._genders.get(self.gender_letter or 'u')

    def gender_letter(self):
        return self.gender_letter


class Prediction:
    def __init__(self, _class: UserClass, features: UserFeatures):
        self._class = _class
        self.features = features

    def real_class(self):
        return self.features.class_value()

    def predicted_class(self):
        return self._class.gender_value()

    def is_right(self):
        return self.predicted_class() == self.real_class()

    def user_id(self):
        return self.features.user_id
