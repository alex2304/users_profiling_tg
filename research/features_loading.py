from typing import Tuple, List

from data.transferring import DataUploader
from models import FeaturesFromBot
from models import FeaturesFromChat
from models import UserClass
from models import UserFeatures


class FeaturesLoader(DataUploader):
    def __init__(self):
        super(FeaturesLoader, self).__init__()

    def get_all_users_features(self) -> Tuple[List[UserFeatures], List[UserFeatures]]:
        """
        :return: Tuple(users with known class, users with unknown class)
        """
        chats = self.get_chats()
        users = self.get_users()
        bots = self.get_bots()

        users_features = {u.uid: set() for u in users}

        # collect from chats
        for index, user_in_chat in enumerate(self.get_users_in_chats()):
            chat_id, uid, diff, freq, length = (user_in_chat.chat_id,
                                                user_in_chat.user_id,
                                                user_in_chat.entering_difference,
                                                user_in_chat.avg_msg_frequency,
                                                user_in_chat.avg_msg_length)

            if not users_features.get(uid):
                users_features[uid] = set()

            users_features[uid].add(FeaturesFromChat(chat_id, participation=1,
                                                     freq=freq, length=length, diff=diff))

        # collect features from bots
        for user_in_bot in self.get_users_in_bots():
            bot_title, uid, lang = (user_in_bot.bot_title,
                                    user_in_bot.user_id,
                                    user_in_bot.lang)

            if not users_features.get(uid):
                users_features[uid] = set()

            users_features[uid].add(FeaturesFromBot(bot_title, participation=1, language=lang))

        known, unknown = [], []

        # include user classes
        users_genders = self.get_user_genders()

        # update features sets with chats and bots, where user doesn't participate
        not_part_chats_bots = {FeaturesFromChat(chat.cid, 0) for chat in chats}
        not_part_chats_bots.update([FeaturesFromBot(bot.title, 0) for bot in bots])

        for user_id, user_features in users_features.items():
            user_features.update(not_part_chats_bots)

            # decide whether user has known or unknown class
            user_gender = users_genders.get(user_id)

            if user_gender == 'u':
                unknown.append(UserFeatures(user_id,
                                            UserClass(user_id, user_gender).gender_value(),
                                            *[f.to_values_list()
                                              for f in sorted(user_features)]))
            elif user_gender:
                known.append(UserFeatures(user_id,
                                          UserClass(user_id, user_gender).gender_value(),
                                          *[f.to_values_list()
                                            for f in sorted(user_features)]))

        return known, unknown

    def get_training_features(self):
        known, _ = self.get_all_users_features()

        return known
        # return [[0, 0, 0],  # b || !c
        #         [0, 0, 1],
        #         [0, 1, 0],
        #         [1, 0, 1],
        #         [1, 1, 0],
        #         [1, 1, 1]], [0, 0, 0, 1, 1, 1]

    def get_unknown_features(self):
        _, unknown = self.get_all_users_features()

        return unknown
