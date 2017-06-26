import json
from datetime import datetime
from typing import Set

from models.base_entities import Message, Chat, User, BaseEntity


class UserInChat(BaseEntity):
    def __hash__(self):
        return hash(str(self.user_id) + str(self.chat_id))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __init__(self, chat_id, user_id, entering_difference, avg_msg_frequency, avg_msg_length):
        super().__init__()
        self.chat_id = chat_id
        self.user_id = user_id

        self.entering_difference = entering_difference
        self.avg_msg_frequency = avg_msg_frequency
        self.avg_msg_length = avg_msg_length


class ChatsEntities(BaseEntity):
    def __eq__(self, other):
        pass

    def __hash__(self):
        pass

    def __init__(self, chats: Set[Chat]=None, users: Set[User]=None, messages: Set[Message]=None,
                 users_in_chats: Set[UserInChat]=None):
        super().__init__()

        self.messages = messages or set()
        self.chats = chats or set()
        self.users = users or set()

        self.users_in_chats = users_in_chats or set()

    # TODO: pickle
    # def serialize(self):
    #     return json.dumps({
    #         "users": [u.serialize() for u in self.users if u],
    #         "messages": [m.serialize() for m in self.messages if m],
    #         "chats": [c.serialize() for c in self.chats if c],
    #     })
    #
    # def deserialize(self, _json):
    #     self.messages = [Message(**params) for params in _json['messages']]
    #     self.chats = [Chat(**params) for params in _json['chats']]
    #     self.users = [User(**params) for params in _json['users']]
    #
    #     self.users_in_chats = []
    # def from_file(self, filename):
    #     self.deserialize(
    #         json.load(
    #             open(filename, 'r', encoding='utf-8')
    #         )
    #     )
    #
    # def to_file(self, filename):
    #     # with open(filename, 'w', encoding='utf-8') as f:
    #     with open(filename, 'wb') as f:
    #         f.write(self.serialize())
