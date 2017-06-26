

class BaseFeatures:
    def __init__(self, _class=None, *features):
        super().__init__()

        self._features = features
        self._class = _class

    def features_list(self):
        return self._features

    def class_value(self):
        return self._class
