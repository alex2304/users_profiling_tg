from typing import Set

from models import ChatsEntities, Bot, UserInBot
from parsing import DataParser
from parsing import DataUploader
from telegram import SettingsHolder, TelegramDataLoader

tg_config_file_path = "tg_settings/tg_config"
target_chats_file_path = "tg_settings/target_chats"


def upload_chat_entities():
    # load tg_settings and initialize Telegram client
    settings_holder = SettingsHolder(tg_config_file_path, target_chats_file_path)
    tg_client = TelegramDataLoader(**settings_holder.get_tg_settings())

    # download information about chats
    entities = tg_client.get_chats_entities(settings_holder.get_target_chats())

    return entities


class DataActions:
    actions_description = '''
    Choose what and from what u want to transfer to SQL DB:
    1 - Static data (bots, chats): from config files
    2 - Users' data (users, messages, users_in_chats): from Telegram

    3 - Users' participation in bots (users_in_bots): from MongoDB
    4 - Buses clicks data (bus_clicks): from file raw_data
    5 - Placed ads data (placed_ads): from MongoDB
    6 - Food orders data (food_orders): from MongoDB

    0 - Exit

    > '''

    # parser to parse from different formats
    parser = DataParser()
    # uploader for uploading in unified format (sql)
    uploader = DataUploader()

    @staticmethod
    def perform(action_number: str):
        if not action_number or not action_number.isdigit():
            return 'Unknown action number'

        return 'Action performed successfully'


if __name__ == '__main__':
    _menu_text = DataActions.actions_description
    _user_response = ''

    while True:
        _user_response = input(_menu_text)

        if _user_response in ('exit', '0'):
            break

        result_message = DataActions.perform(_user_response)
        input('\n%s\n(press any key to continue)\n' % result_message)
