import os
import traceback
from typing import Set

from data.transferring import DataParser
from data.transferring.uploading import DataUploader
from models import BaseEntity, Bot, UserInBot, Chat, User, Message, BusClick, PlacedAd, FoodOrder
from models import ChatsEntities
from models import UserInChat


class TransferringActions:
    actions_description = '''
    Choose what and from what u want to transfer to SQL DB:
    1 - Chats and Users' data (chats, users, messages, users_in_chats): from config files and Telegram
    2 - Bots and users in bots (bots, users_in_bots): from config file and MongoDB

    3 - Buses clicks data (bus_clicks): from file raw_data
    4 - Placed ads data (placed_ads): from MongoDB
    5 - Food orders data (food_orders): from MongoDB

    0 - Exit

    > '''

    # parser to parse from different formats
    parser = DataParser()

    # uploader for uploading in unified format (sql)
    uploader = DataUploader()

    @classmethod
    def insert_entities(cls, entities: Set[BaseEntity]):
        for e in entities:
            cls.uploader.insert_entity(e)

    @classmethod
    def perform(cls, action_number: str):
        if not action_number or not action_number.isdigit():
            return 'Wrong action number'

        result_str = 'Unknown action number'
        action_number = int(action_number)

        # upload chats entities (chats, users, messages, users_in_chats)
        if action_number == 1:
            # TODO: move serializing to TG client
            _serialized_filename = 'serialized_chat_entities'

            # try to load serialized entities (if exists)
            if os.path.exists(_serialized_filename):
                chat_entities = ChatsEntities()
                chat_entities.from_file(_serialized_filename)

            # or load from Telegram and save to temp file
            else:
                chat_entities = cls.parser.get_chat_entities()
                chat_entities.to_file(_serialized_filename)

            # clear old and upload new chat entities to DB
            try:
                cls.uploader.clear_tables(Chat, User, Message, UserInChat)
                cls.uploader.upload_chats_entities(chat_entities)

            except Exception as e:
                print(traceback.format_tb(e.__traceback__))
                result_str = 'Error uploading chat entities. Saved at %s' % _serialized_filename

            else:
                result_str = 'Chat entities were uploaded'

                # if there weren't any error - remove serialized file
                if os.path.exists(_serialized_filename):
                    os.remove(_serialized_filename)

        # upload bots and users in bots
        elif action_number == 2:
            bots, users_in_bots = cls.parser.get_bots(), cls.parser.get_users_in_bots()

            cls.uploader.clear_tables(Bot, UserInBot)
            cls.insert_entities(bots)
            cls.insert_entities(users_in_bots)

            result_str = 'Bots and users were uploaded'

        # upload bus clicks
        elif action_number == 3:
            clicks = cls.parser.get_bus_clicks()

            cls.uploader.clear_tables(BusClick)
            cls.insert_entities(clicks)

            result_str = 'Buses clicks users were uploaded'

        # upload placed ads
        elif action_number == 4:
            placed_ads = cls.parser.get_placed_ads()

            cls.uploader.clear_tables(PlacedAd)
            cls.insert_entities(placed_ads)

            result_str = 'Placed ads users were uploaded'

        # upload food orders
        elif action_number == 5:
            food_orders = cls.parser.get_food_orders()

            cls.uploader.clear_tables(FoodOrder)
            cls.insert_entities(food_orders)

            result_str = 'Food orders were uploaded'

        return result_str


if __name__ == '__main__':
    _menu_text = TransferringActions.actions_description
    _user_response = ''

    while True:
        _user_response = input(_menu_text)

        if _user_response in ('exit', '0'):
            break

        result_message = TransferringActions.perform(_user_response)
        input('\n%s\n(press any key to continue)\n' % result_message)
