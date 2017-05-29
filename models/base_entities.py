from abc import abstractmethod
from datetime import datetime
from typing import Set

# classes which will be imported when using "from . import *"
__all__ = ["BaseModel", "User", "Chat", "Message", "Bot", "UserInBot", "FoodOrder", "BusClick", "PlacedAd"]


class BaseModel:

    def __init__(self):
        self.__dict__ = {}

    def serialize(self):
        return self.__dict__

    def deserialize(self, _json):
        self.__dict__ = _json

    @abstractmethod
    def __eq__(self, other):
        pass

    @abstractmethod
    def __hash__(self):
        pass


class User (BaseModel):
    def __init__(self, uid: int, first_name: str, last_name: str=None, username: str=None):
        super().__init__()
        self.last_name = last_name
        self.first_name = first_name
        self.uid = uid
        self.username = username

    def __eq__(self, other):
        return other.uid == self.uid

    def __hash__(self):
        return self.uid


class Chat(BaseModel):
    def __init__(self, cid: int, title: str, members_count: int, users_ids: Set[int]):
        super().__init__()
        self.users_ids = list(users_ids)
        self.title = title
        self.members_count = members_count
        self.cid = cid

    def __eq__(self, other):
        return other.cid == self.cid

    def __hash__(self):
        return self.cid


class Message(BaseModel):
    def __init__(self, msg_id: int, text: str, date: int, author_id: int, chat_id: int):
        super().__init__()
        self.chat_id = chat_id
        self.author_id = author_id
        self.date = str(date)
        self.text = text
        self.msg_id = msg_id

    def __eq__(self, other):
        return self.msg_id == other.msg_id and self.author_id == other.author_id and self.chat_id == other.chat_id

    def __hash__(self):
        return int(str(self.chat_id) + str(self.author_id) + str(self.msg_id))


class Bot(BaseModel):

    def __init__(self, title: str, members_count: int):
        super().__init__()
        self.members_count = members_count
        self.title = title

    def __eq__(self, other):
        return self.title == other.title

    def __hash__(self):
        return hash(self.title)


class UserInBot(BaseModel):
    def __init__(self, bot_title: str, user_id: int, lang: str):
        super().__init__()
        self.lang = lang
        self.user_id = user_id
        self.bot_title = bot_title

    def __eq__(self, other):
        return self.bot_title == other.bot_title and self.user_id == other.user_id

    def __hash__(self):
        return hash(self.bot_title + str(self.user_id))


class FoodOrder(BaseModel):
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


class BusClick(BaseModel):
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


class PlacedAd(BaseModel):
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
