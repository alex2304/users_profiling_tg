from typing import List

import postgresql
import re
from postgresql.exceptions import Error

from models import User, Chat, Message, ChatsEntities, Bot, UserInBot, FoodOrder, BusClick, PlacedAd, BaseEntity

# address to connect
from models import UserInChat

postgres_db_address = 'pq://postgres:postgres@localhost:5432/Telegram Data'


# TODO: change format
# TODO: change SQL schema
class DataUploader:
    def __init__(self):
        self.db = postgresql.open(postgres_db_address)

        self._insert_user = self.db.prepare('SELECT * FROM insert_user($1, $2, $3, $4)')
        self._insert_chat = self.db.prepare('INSERT INTO '
                                            'chats(chat_id, title, members_count, messages_count, creation_date) '
                                            'VALUES ($1, $2, $3, $4, $5)')
        self._insert_user_in_chat = self.db.prepare('SELECT * FROM insert_user_in_chat($1, $2, $3, $4, $5)')
        self._insert_message = self.db.prepare('SELECT * FROM insert_message($1, $2, $3, $4, $5)')

        self._insert_bot = self.db.prepare('INSERT INTO bots(title, members_count) VALUES ($1, $2)')
        self._insert_user_in_bot = self.db.prepare('SELECT * FROM insert_user_in_bot($1, $2, $3)')

        self._insert_food_order = self.db.prepare('SELECT * FROM insert_food_order($1, $2, $3, $4, $5)')
        self._insert_bus_click = self.db.prepare('SELECT * FROM insert_bus_click($1, $2, $3, $4, $5)')
        self._insert_placed_ad = self.db.prepare('SELECT * FROM insert_placed_ad($1, $2, $3, $4, $5, $6)')

        self._insert_user_gender = self.db.prepare('INSERT INTO users_genders VALUES ($1, $2)')
        self._insert_predicted_gender = self.db.prepare('INSERT INTO predicted_genders VALUES ($1, $2)')

    def __del__(self):
        self.db.close()

    def insert_entity(self, e: BaseEntity):
        try:
            if isinstance(e, User):
                self.insert_user(e)

            elif isinstance(e, Chat):
                self.insert_chat(e)

            elif isinstance(e, Bot):
                self.insert_bot(e)

            elif isinstance(e, Message):
                self.insert_message(e)

            elif isinstance(e, UserInBot):
                self.insert_user_in_bot(e)

            elif isinstance(e, BusClick):
                self.insert_bus_click(e)

            elif isinstance(e, FoodOrder):
                self.insert_food_order(e)

            elif isinstance(e, PlacedAd):
                self.insert_placed_ad(e)

            elif isinstance(e, UserInChat):
                self.insert_users_in_chat([e])

            else:
                raise TypeError('Unknown entity type %s' % str(type(e)))

        except Error as e:
            print(e)
            raise Error('Error inserting entity %s' % str(type(e)))

    def insert_user(self, user: User):
        self._insert_user(user.uid, user.first_name, user.last_name, user.username)

    def insert_chat(self, chat: Chat):
        self._insert_chat(chat.cid, chat.title, chat.members_count, chat.messages_count, chat.creation_date)

    def insert_users_in_chat(self, users_in_chats: List[UserInChat]):
        for entry in users_in_chats:
            self._insert_user_in_chat(entry.chat_id, entry.user_id,
                                      entry.entering_difference, entry.avg_msg_frequency, entry.avg_msg_length)

    def insert_message(self, msg: Message):
        self._insert_message(msg.msg_id, msg.text, msg.date, msg.chat_id, msg.author_id)

    def insert_bot(self, bot: Bot):
        self._insert_bot(bot.title, bot.members_count)

    def insert_user_in_bot(self, user_in_bot: UserInBot):
        self._insert_user_in_bot(user_in_bot.bot_title, user_in_bot.user_id, user_in_bot.lang)

    def insert_food_order(self, food_order: FoodOrder):
        self._insert_food_order(food_order.user_id,
                                food_order.food_category, food_order.food_item, food_order.quantity,
                                food_order.timestamp)

    def insert_bus_click(self, bus_click: BusClick):
        self._insert_bus_click(bus_click.user_id,
                               bus_click.click_timestamp,
                               bus_click.route_id, bus_click.route_start_time,
                               bus_click.shuttle_id)

    def insert_placed_ad(self, placed_ad: PlacedAd):
        self._insert_placed_ad(placed_ad.user_id,
                               placed_ad.placed_timestamp,
                               placed_ad.category_title, placed_ad.ad_type,
                               placed_ad.views_count, placed_ad.likes_count)

    def upload_chats_entities(self, entities: ChatsEntities):
        try:
            with self.db.xact():
                # insert users
                users = entities.users
                for u in users:
                    self.insert_user(u)

            with self.db.xact():
                # insert chats and users in chats
                chats = entities.chats
                for c in chats:
                    self.insert_chat(c)

            with self.db.xact():
                # insert messages
                messages = entities.messages
                for m in messages:
                    self.insert_message(m)

            with self.db.xact():
                # insert users in chats
                users_in_chats = entities.users_in_chats
                self.insert_users_in_chat(users_in_chats)

        except Error as e:
            print(e)
            raise Exception('Error uploading chats entities %s' % str(entities))

    @staticmethod
    def _table_title_by_type(entity_type: BaseEntity):
        if entity_type is User:
            table_title = 'users'

        elif entity_type is Chat:
            table_title = 'chats'

        elif entity_type is Bot:
            table_title = 'bots'

        elif entity_type is Message:
            table_title = 'messages'

        elif entity_type is UserInBot:
            table_title = 'users_in_bots'

        elif entity_type is BusClick:
            table_title = 'buses_clicks'

        elif entity_type is FoodOrder:
            table_title = 'food_orders'

        elif entity_type is PlacedAd:
            table_title = 'placed_ads'

        elif entity_type is UserInChat:
            table_title = 'users_in_chats'

        else:
            raise TypeError('Unknown entity type %s' % str(entity_type))

        return table_title

    def clear_tables(self, *tables_types):
        table_title = ''
        try:
            with self.db.xact():
                for t in tables_types:
                    table_title = self._table_title_by_type(t)
                    self.db.execute("DELETE FROM %s *;" % table_title)

        except Error as e:
            print(e)
            raise Exception('Error clearing table %s' % table_title)

    def get_users_in_chats(self):
        schema = 'chat_id', 'user_id', 'entering_difference', 'avg_msg_frequency', 'avg_msg_length'
        tuples = self.db.query('SELECT * FROM users_in_chats')

        return [UserInChat(**dict(zip(schema, t))) for t in tuples]

    def get_users_in_bots(self):
        schema = 'bot_title', 'user_id', 'lang'
        tuples = self.db.query('SELECT * FROM users_in_bots')

        for t in tuples:
            yield UserInBot(**dict(zip(schema, t)))

    def get_chats(self):
        schema = 'cid', 'title', 'members_count', 'messages_count', 'creation_date'
        tuples = self.db.query('SELECT * FROM chats')

        for t in tuples:
            yield Chat(**dict(zip(schema, t)))

    def get_users(self):
        # miss 'tg_id' field
        schema = 'uid', 'tg_id', 'first_name', 'last_name', 'username'
        tuples = self.db.query('SELECT * FROM users')

        for t in tuples:
            yield User(**dict(zip(schema, t)))

    def get_bots(self):
        schema = 'title', 'members_count'
        tuples = self.db.query('SELECT * FROM bots')

        for t in tuples:
            yield Bot(**dict(zip(schema, t)))

    def upload_users_genders(self):
        users = self.get_users()

        for user in users:
            self._insert_user_gender(user.uid, user.get_gender())

    def get_user_genders(self):
        tuples = self.db.query('SELECT * FROM users_genders')

        return {t[0]: t[1] for t in tuples}

    def save_predicted_genders(self, users_genders):
        self.db.execute('DELETE FROM predicted_genders *;')

        for user_id, gender in users_genders.items():
            self._insert_predicted_gender(user_id, gender)

if __name__ == '__main__':
    uploader = DataUploader()

    uploader.upload_users_genders()
