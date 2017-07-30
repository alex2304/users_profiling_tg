import os
import pickle
import re
from typing import Tuple, List, Dict, Set

from data.transferring import DataUploader
from models import FeaturesFromBot
from models import FeaturesFromChat
from models import UserClass
from models import UserSample
from models.prediction import Features, MessageSample
from research.text_processing.features_gen import TextFeaturesExtractor
from research.text_processing.mystem import TextProcessor


class FeaturesExtractor(DataUploader):
    def __init__(self):
        super(FeaturesExtractor, self).__init__()

    def _get_chats_bots_features(self, existed_users_features: Dict[int, Set[Features]]=None) -> Dict[int, Set[Features]]:
        """
        Adds features from chats and bots to the existing :users_features dict
        """
        chats = self.get_chats()
        users = self.get_users()
        bots = self.get_bots()

        # if passed user features dict is None - create it from scratch
        users_features = existed_users_features or {u.uid: set() for u in users}

        # collect from chats (only with participation)
        for index, user_in_chat in enumerate(self.get_users_in_chats()):
            chat_id, uid, diff, freq, length = (user_in_chat.chat_id,
                                                user_in_chat.user_id,
                                                user_in_chat.entering_difference,
                                                user_in_chat.avg_msg_frequency,
                                                user_in_chat.avg_msg_length)

            if users_features.get(uid) is None:
                users_features[uid] = set()
                print('Warning: user with uid %d was absent; added. (Chats features extraction) ' % uid)

            users_features[uid].add(FeaturesFromChat(chat_id, participation=1,
                                                     freq=freq, length=length, diff=diff))

        # collect features from bots (only with participation)
        for user_in_bot in self.get_users_in_bots():
            bot_title, uid, lang = (user_in_bot.bot_title,
                                    user_in_bot.user_id,
                                    user_in_bot.lang)

            if users_features.get(uid) is None:
                users_features[uid] = set()
                print('Warning: user with uid %d was absent; added. (Bots features extraction) ' % uid)

            users_features[uid].add(FeaturesFromBot(bot_title, participation=1, language=lang))

        # for each chat and bot, create features without participation
        not_part_chats_bots = {FeaturesFromChat(chat.cid, 0) for chat in chats}
        not_part_chats_bots.update([FeaturesFromBot(bot.title, 0) for bot in bots])

        # for each user, add features for that chats and bots, where user is not presented
        for user_id, user_features in users_features.items():
            user_features.update(not_part_chats_bots)

        return users_features

    def _get_food_orders_features(self, existed_users_features: Dict[int, Set[Features]]=None) -> Dict[int, Set[Features]]:
        """
        Adds features from food orders to the existing :users_features dict
        """
        users = self.get_users()
        food_orders = self.get_food_orders()

        # create set of all the food items
        all_food_items = {order.food_item for order in food_orders if order.food_item}

        # create dict of users ids and their food orders count (for each food item)
        ordered_items_count = {u.uid: {food_item: 0
                                       for food_item in all_food_items}
                               for u in users}

        # count number of orders of each food item by each user
        for order in food_orders:
            # omit orders with unknown food items
            if not order.food_item:
                continue

            if ordered_items_count.get(order.user_id) is None:
                ordered_items_count[order.user_id] = {food_item: 0 for food_item in all_food_items}
                print('Warning: user with uid %d was absent; added. (Food orders features extraction) ' % order.user_id)

            # increase count of ordered food item by quantity value
            ordered_items_count[order.user_id][order.food_item] += order.quantity

        # if passed user features dict is None - create it from scratch
        users_features = existed_users_features or {u.uid: set() for u in users}

        # convert orders counts to features list
        for uid, orders_count in ordered_items_count.items():
            if users_features.get(uid) is None:
                users_features[uid] = set()
                print('Warning: user with uid %d was absent; added. (Food orders features extraction) ' % uid)

            features = []

            # create list of features (sort food items by titles)
            for food_item in sorted(orders_count.keys()):
                # each feature - number of orders of an item
                features.append(orders_count[food_item])

            # add features to the user's features
            users_features[uid].add(Features(*features))

        return users_features

    def _get_placed_ads_features(self, existed_users_features: Dict[int, Set[Features]]=None) -> Dict[int, Set[Features]]:
        """
        Adds features from placed ads to the existing :users_features dict
        """
        users = self.get_users()
        placed_ads = self.get_placed_ads()

        # create set of all the ads categories (category title + ad type)
        all_categories = {placed_ad.category_title + placed_ad.ad_type for placed_ad in placed_ads}

        # create dict of users ids and count of their ads in each category
        placed_ads_count = {u.uid: {category: 0
                                    for category in all_categories}
                            for u in users}

        # count number of placed ads in each ads categories by each user
        for ad in placed_ads:
            if placed_ads_count.get(ad.user_id) is None:
                placed_ads_count[ad.user_id] = {category: 0 for category in all_categories}
                print('Warning: user with uid %d was absent; added. (Placed ads features extraction) ' % ad.user_id)

            # increase count of placed ads in the category by 1
            placed_ads_count[ad.user_id][ad.category_title + ad.ad_type] += 1

        # if passed user features dict is None - create it from scratch
        users_features = existed_users_features or {u.uid: set() for u in users}

        # convert placed ads to features list
        for uid, ads_count in placed_ads_count.items():
            if users_features.get(uid) is None:
                users_features[uid] = set()
                print('Warning: user with uid %d was absent; added. (Placed ads features extraction) ' % uid)

            features = []

            # create list of features (sort categories by titles)
            for category in sorted(ads_count.keys()):
                # each feature - number of
                features.append(ads_count[category])

            # add features to the user's features
            users_features[uid].add(Features(*features))

        return users_features

    def _get_buses_clicks_features(self, existed_users_features: Dict[int, Set[Features]]=None) -> Dict[int, Set[Features]]:
        """
        Adds features from bus clicks to the existing :users_features dict
        """
        users = self.get_users()
        buses_clicks = self.get_buses_clicks()

        all_routes = {click.route_id for click in buses_clicks}

        clicks_count = {u.uid: {route: 0
                                for route in all_routes}
                        for u in users}

        for click in buses_clicks:
            if clicks_count.get(click.user_id) is None:
                clicks_count[click.user_id] = {route: 0 for route in all_routes}
                print('Warning: user with uid %d was absent; added. (Placed ads features extraction) ' % click.user_id)

            clicks_count[click.user_id][click.route_id] += 1

        users_features = existed_users_features or {u.uid: set() for u in users}

        for uid, clicks_count in clicks_count.items():
            if users_features.get(uid) is None:
                users_features[uid] = set()
                print('Warning: user with uid %d was absent; added. (Placed ads features extraction) ' % uid)

            features = []

            for route in sorted(clicks_count.keys()):
                features.append(clicks_count[route])

            # add features to the user's features
            users_features[uid].add(Features(*features))

        return users_features

    def get_all_users_features(self) -> Tuple[List[UserSample], List[UserSample]]:
        """
        Returns tuple of features of users with known and unknown classes
        """
        known, unknown = [], []

        # get all kinds of features
        users_features = self._get_chats_bots_features()
        users_features = self._get_food_orders_features(existed_users_features=users_features)
        users_features = self._get_placed_ads_features(existed_users_features=users_features)
        users_features = self._get_buses_clicks_features(existed_users_features=users_features)

        # get classes of users
        users_genders = self.get_users_genders()

        # create instances of UserFeatures for known and unknown features
        for user_id, user_features in users_features.items():
            # decide whether user has known or unknown class
            user_gender = users_genders.get(user_id)

            # features become sorted (see Features class to understand why)
            if user_gender == 'u':
                unknown.append(UserSample(user_id,
                                          UserClass(user_id, user_gender).gender_value(),
                                          *[f.to_values_list()
                                              for f in sorted(user_features)]))
            elif user_gender:
                known.append(UserSample(user_id,
                                        UserClass(user_id, user_gender).gender_value(),
                                        *[f.to_values_list()
                                            for f in sorted(user_features)]))

        return known, unknown

    def get_users_training_features(self):
        known, _ = self.get_all_users_features()

        return known

    def get_users_unknown_features(self):
        _, unknown = self.get_all_users_features()

        return unknown

    def get_messages_features(self, from_file=False, save_to_file=True):
        _dump_filepath = os.path.join(os.path.dirname(__file__), 'model_dump/messages_features.p')

        if from_file:
            if not os.path.exists(_dump_filepath):
                raise FileNotFoundError('%s does not exists, but was required' % _dump_filepath)
 
            return pickle.load(open(_dump_filepath, 'rb'))

        messages = list(filter(lambda m: re.match('.*[а-яА-Яa-zA-Z]+.*', m.text), self.get_messages()))
        users = self.get_users()

        users_messages = {u.uid: list() for u in users}

        # stem texts of all the messages
        with TextProcessor() as tp:
            stemmed_texts = tp.stemming([m.text for m in messages])

        # sort stemmed messages texts by their authors
        for msg, stemmed_text in zip(messages, stemmed_texts):
            if users_messages.get(msg.author_id) is None:
                users_messages[msg.author_id] = set()
                print('Warning: user with uid %d was absent; added. (Messages features extraction) ' % msg.author_id)

            users_messages[msg.author_id].append(stemmed_text)

        fe = TextFeaturesExtractor(n_gram=1, max_features=5000, min_occurrence_rate=2)

        fe.load_vocabulary(stemmed_texts, stemming=False)

        users_genders = self.get_users_genders()

        known, unknown = [], []

        # collect features from text of messages of each user
        for uid, msgs_texts in users_messages.items():
            if not msgs_texts:
                continue

            messages_features = fe.extract_features(msgs_texts, stemming=False)

            user_gender = users_genders.get(uid)

            for msg_number, msg_features in enumerate(messages_features):
                if user_gender == 'u':
                    unknown.append(MessageSample(uid,
                                                 msg_number,
                                                 UserClass.resolve_value(user_gender),
                                                 *msg_features))
                elif user_gender:
                    known.append(MessageSample(uid,
                                               msg_number,
                                               UserClass.resolve_value(user_gender),
                                               *msg_features))

        if save_to_file:
            pickle.dump((known, unknown), open(_dump_filepath, 'wb'))

        return known, unknown

if __name__ == '__main__':
    fe = FeaturesExtractor()

    known, unknown = fe.get_messages_features(from_file=False)
