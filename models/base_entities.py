import os
import pickle
import re
from abc import abstractmethod
from datetime import datetime
from typing import List

__all__ = ["BaseEntity", "User", "Chat", "Message", "Bot", "UserInBot", "FoodOrder", "BusClick", "PlacedAd"]


class BaseEntity:

    def __init__(self):
        self.__dict__ = {}

    # TODO: add try/except
    def serialize(self):
        return pickle.dumps(self)
        # return self.__dict__

    def deserialize(self, _json):
        self.__dict__ = pickle.loads(_json).__dict__
        # self.__dict__ = _json

    def from_file(self, filename):
        # self.deserialize(
        #     json.load(
        #         open(filename, 'r', encoding='utf-8')
        #     )
        # )
        self.__dict__ = pickle.load(open(filename, 'rb')).__dict__

    def to_file(self, filename):
        # with open(filename, 'w', encoding='utf-8') as f:
        with open(filename, 'wb') as f:
            f.write(self.serialize())

    @abstractmethod
    def __eq__(self, other):
        pass

    @abstractmethod
    def __hash__(self):
        pass


class NamesLoader:
    _names_path = os.path.join(os.path.dirname(__file__), 'names')
    _m_filepath, _f_filepath = os.path.join(_names_path, 'males.txt'), os.path.join(_names_path, 'females.txt')

    @classmethod
    def _update_names(cls, m, f):
        # remove duplicates
        m, f = list(set(m)), list(set(f))

        # return sorted
        return sorted(m), sorted(f)

    @classmethod
    def get_m_f_names(cls):
        with open(cls._m_filepath, encoding='utf-8') as f:
            male_names = [name.replace('\n', '').lower().replace('ё', 'е') for name in f if name]

        with open(cls._f_filepath, encoding='utf-8') as f:
            female_names = [name.replace('\n', '').lower().replace('ё', 'е') for name in f if name]

        # return updated
        return cls.update_and_save(male_names, female_names)

    @classmethod
    def update_and_save(cls, m: List[str], f: List[str]):
        m_names, f_names = cls._update_names(m, f)

        with open(cls._m_filepath, encoding='utf-8', mode='w') as f:
            for n in m_names:
                f.write(n)
                f.write('\n')

        with open(cls._f_filepath, encoding='utf-8',  mode='w') as f:
            for n in f_names:
                f.write(n)
                f.write('\n')

        # return updated
        return m_names, f_names


class User(BaseEntity):
    _name_pattern = re.compile('[a-zA-Zа-яА-Я]{3,30}')

    # load names from files
    _names = dict(zip(('m', 'f'), NamesLoader.get_m_f_names()))

    def __init__(self, uid: int, first_name: str, last_name: str=None, username: str=None, **other):
        super().__init__()
        self.last_name = last_name
        self.first_name = first_name
        self.uid = uid
        self.username = username

    def get_gender(self):
        name_str = ' '.join([self.first_name or '', self.last_name or '', self.username or '']).replace('ё', 'е')

        names_parts = re.findall(self._name_pattern, name_str)

        for name_part in names_parts:
            if re.match(self._name_pattern, name_part):
                lower_name = name_part.lower()

                if lower_name in self._names['m']:
                    return 'm'

                elif lower_name in self._names['f']:
                    return 'f'

        return 'u'

    def __eq__(self, other):
        return other.uid == self.uid

    def __hash__(self):
        return self.uid


class Chat(BaseEntity):
    def __init__(self, cid: int, title: str, members_count: int, messages_count: int, creation_date: datetime):
        super().__init__()
        self.cid = cid
        self.title = title
        self.members_count = members_count
        self.messages_count = messages_count

        self.creation_date = creation_date

    def __eq__(self, other):
        return other.cid == self.cid

    def __hash__(self):
        return self.cid


class Message(BaseEntity):
    def __init__(self, msg_id: int, text: str, date: datetime, author_id: int, chat_id: int):
        super().__init__()
        self.chat_id = chat_id
        self.author_id = author_id
        self.date = date
        self.text = text
        self.msg_id = msg_id

    def __eq__(self, other):
        return self.msg_id == other.msg_id and self.author_id == other.author_id and self.chat_id == other.chat_id

    def __hash__(self):
        return int(str(self.chat_id) + str(self.author_id) + str(self.msg_id))


class Bot(BaseEntity):

    def __init__(self, title: str, members_count: int):
        super().__init__()
        self.members_count = members_count
        self.title = title

    def __eq__(self, other):
        return self.title == other.title

    def __hash__(self):
        return hash(self.title)


class UserInBot(BaseEntity):
    def __init__(self, bot_title: str, user_id: int, lang: str):
        super().__init__()
        self.lang = lang
        self.user_id = user_id
        self.bot_title = bot_title

    def __eq__(self, other):
        return self.bot_title == other.bot_title and self.user_id == other.user_id

    def __hash__(self):
        return hash(self.bot_title + str(self.user_id))


class FoodOrder(BaseEntity):
    def __init__(self, user_id: int, food_category: str, food_item: str, quantity: int, timestamp: datetime):
        super().__init__()
        self.user_id = user_id
        self.food_category = food_category
        self.food_item = food_item
        self.timestamp = timestamp
        self.quantity = quantity

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(str(self.user_id) + (self.food_category or 'Unknown_category') + (self.food_item or 'Unknown_item'))


class BusClick(BaseEntity):
    def __init__(self, user_id: int, click_timestamp: datetime, route_id: str, shuttle_id: int,
                 route_start_time: datetime):
        super().__init__()
        self.user_id = user_id
        self.click_timestamp = click_timestamp
        self.route_id = route_id
        self.shuttle_id = shuttle_id
        self.route_start_time = route_start_time

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(str(self.user_id) + str(self.click_timestamp) + str(self.shuttle_id))


class PlacedAd(BaseEntity):
    def __init__(self, user_id: int, placed_timestamp: datetime, category_title: str, ad_type: str,
                 views_count: int, likes_count: int):
        super().__init__()
        self.user_id = user_id
        self.ad_type = ad_type
        self.category_title = category_title
        self.placed_timestamp = placed_timestamp
        self.views_count = views_count
        self.likes_count = likes_count

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(str(self.user_id) + str(self.placed_timestamp) + str(self.ad_type) + str(self.category_title))

if __name__ == '__main__':
    NamesLoader.update_and_save(**User._names)