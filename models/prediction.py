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


# for an ability to order objects of the class
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
        self_class, other_class = self.__class__.__name__, other.__class__.__name__

        # instances of the same class
        if self_class == other_class:
            if isinstance(self, FeaturesFromChat):
                return 1 if self.chat_id > other.chat_id else -1

            elif isinstance(self, FeaturesFromBot):
                return 1 if self.bot_title > other.bot_title else -1

            else:
                raise NotImplementedError('Not implemented comparison of features for the class %s ' % self_class)

        # instances of different classes
        else:
            # sort by class names
            return 1 if self_class > other_class else -1

    def to_values_list(self):
        return self.features

    def __eq__(self, other):
        self_class, other_class = self.__class__.__name__, other.__class__.__name__

        if self_class == other_class:
            if isinstance(self, FeaturesFromChat):
                return self.chat_id == other.chat_id

            elif isinstance(self, FeaturesFromBot):
                return self.bot_title == other.bot_title

            else:
                raise NotImplementedError('Not implemented equality op. of features for the class %s ' % self_class)

        else:
            return False

    def __gt__(self, other):
        self_class, other_class = self.__class__.__name__, other.__class__.__name__

        if self_class == other_class:
            if isinstance(self, FeaturesFromChat):
                return self.chat_id > other.chat_id

            elif isinstance(self, FeaturesFromBot):
                return self.bot_title > other.bot_title

            else:
                raise NotImplementedError('Not implemented greater op. of features for the class %s ' % self_class)

        else:
            return self_class > other_class

    def __hash__(self):
        return hash(self.features)


class FeaturesFromChat(Features):
    def __cmp__(self, other):
        pass

    def __init__(self, chat_id, participation, freq=0, length=0, diff=0):
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
        'u': 2
    }

    def _resolve_letter(self, gender_value):
        for k, v in self._genders.items():
            if gender_value == v:
                return k

        print('Warning: unknown gender letter for value %s. Marked as unknown gender.' % str(gender_value))

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
