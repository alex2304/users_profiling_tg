

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
