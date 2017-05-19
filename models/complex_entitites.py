import json
from typing import Set

from models.base_entities import Message, Chat, User


class ChatsEntities:
    def __init__(self, users: Set[User]=None, chats: Set[Chat]=None, messages: Set[Message]=None):
        self.messages = messages or set()
        self.chats = chats or set()
        self.users = users or set()

    def serialize(self, file_path='serialized.json'):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({
                "users": [u.serialize() for u in self.users if u],
                "messages": [m.serialize() for m in self.messages if m],
                "chats": [c.serialize() for c in self.chats if c],
            }, f, ensure_ascii=False)

        print("serialized!")

    @staticmethod
    def deserialize(file_path='serialized.json'):
        e_holder = ChatsEntities()

        with open(file_path, 'r', encoding='utf-8') as f:
            from_file = json.load(f)

            e_holder.messages = [Message(**params) for params in from_file['messages']]
            e_holder.chats = [Chat(**params) for params in from_file['chats']]
            e_holder.users = [User(**params) for params in from_file['users']]

        print('deserialized!')

        return e_holder
