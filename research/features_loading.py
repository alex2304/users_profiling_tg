from typing import Tuple, List, Any, Generator, Iterable

from data.transferring import DataUploader
from models import FeaturesFromBot
from models import FeaturesFromChat
from models import UserFeatures


class FeaturesLoader(DataUploader):
    def __init__(self):
        super(FeaturesLoader, self).__init__()

    def _get_all_users_features(self, include_classes=False) -> List[UserFeatures]:
        chats = self.get_chats()
        users = self.get_users()
        bots = self.get_bots()

        users_features = {u.uid: set() for u in users}

        # collect from chats
        for user_in_chat in self.get_users_in_chats():
            chat_id, uid, diff, freq, length = (user_in_chat.chat_id,
                                                user_in_chat.user_id,
                                                user_in_chat.entering_difference,
                                                user_in_chat.avg_msg_frequency,
                                                user_in_chat.avg_msg_length)

            if not users_features.get(uid):
                users_features[uid] = set()

            users_features[uid].add(FeaturesFromChat(chat_id, participation=1, freq=freq, length=length, diff=diff))

        # collect features from bots
        for user_in_bot in self.get_users_in_bots():
            bot_title, uid, lang = (user_in_bot.bot_title,
                                    user_in_bot.user_id,
                                    user_in_bot.lang)

            if not users_features.get(uid):
                users_features[uid] = set()

            users_features[uid].add(FeaturesFromBot(bot_title, participation=0, language=lang))

        # update features sets with chats and bots, where user doesn't participate
        not_part_chats_bots = {FeaturesFromChat(chat.cid, 0) for chat in chats}
        not_part_chats_bots.update([FeaturesFromBot(bot.title, 0) for bot in bots])

        for user_features in users_features.values():
            user_features.update(not_part_chats_bots)

        return [UserFeatures(user_id, None,
                             *[f.to_values_list() for f in sorted(user_features)])
                for user_id, user_features in users_features.items()]

    def get_training_features(self):
        return self._features_to_xy(self._get_all_users_features(include_classes=True))
        # return [[0, 0, 0],  # b || !c
        #         [0, 0, 1],
        #         [0, 1, 0],
        #         [1, 0, 1],
        #         [1, 1, 0],
        #         [1, 1, 1]], [0, 0, 0, 1, 1, 1]

    def get_features(self):
        return self._features_to_x(self._get_all_users_features())

    @staticmethod
    def _features_to_x(features: Iterable) -> List[List[Any]]:
        return [f.features_list() for f in features]

    @staticmethod
    def _features_to_xy(features: Iterable) -> Tuple[List[List[Any]], List[Any]]:
        x, y = [], []

        for f in features:
            x.append(f.features_list())
            y.append(f.class_value())

        return x, y

    @staticmethod
    def xy_to_features(x: List[List[Any]], y: List[Any]) -> List[UserFeatures]:
        return [UserFeatures(_class, _features) for _features, _class in zip(x, y)]

if __name__ == '__main__':
    f_loader = FeaturesLoader()

    users_features = f_loader._get_all_users_features()

    print(len(users_features))
