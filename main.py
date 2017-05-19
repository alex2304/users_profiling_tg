from typing import Set

from db import MongoDB, PostgresDB

from models import ChatsEntities, Bot, UserInBot
from telegram import SettingsHolder, TelegramDataLoader

tg_config_file_path = "tg_settings/tg_config"
target_chats_file_path = "tg_settings/target_chats"


# ============= Chats and users ================

def retrieve_chat_entities() -> ChatsEntities:
    # load tg_settings and initialize Telegram client
    settings_holder = SettingsHolder(tg_config_file_path, target_chats_file_path)
    tg_client = TelegramDataLoader(**settings_holder.get_tg_settings())

    # download information about chats
    entities = tg_client.get_chats_entities(settings_holder.get_target_chats())

    return entities


def upload_chats_entities(chats_entities: ChatsEntities):
    db = PostgresDB()

    db.upload_chats_entities(chats_entities)

    db.close()


# ============= Bots and users ================

def retrieve_bots() -> Set[Bot]:
    db = MongoDB()

    return db.get_bots()


def retrieve_users_in_bots() -> Set[UserInBot]:
    db = MongoDB()

    return db.get_users_in_bots()


def upload_bots(bots: Set[Bot]):
    db = PostgresDB()

    for bot in bots:
        db.insert_bot(bot)

    db.close()


def upload_users_in_bots(users_in_bots: Set[UserInBot]):
    db = PostgresDB()

    for u_in_bot in users_in_bots:
        db.insert_user_in_bot(u_in_bot)

    db.close()


def upload_food_orders():
    mongo = MongoDB()
    relational = PostgresDB()

    food_orders = mongo.get_food_orders()

    for food_order in food_orders:
        relational.insert_food_order(food_order)

    relational.close()


if __name__ == '__main__':
    pass
    # TODO: place here what you want to perform
