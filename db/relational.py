import postgresql

from models import User, Chat, Message, ChatsEntities, Bot, UserInBot, FoodOrder, BusClick, PlacedAd

# address to connect
postgres_db_address = 'pq://postgres:postgres@localhost:5432/Telegram Data'


class PostgresDB:
    def close(self):
        self.db.close()

    def __init__(self):
        self.db = postgresql.open(postgres_db_address)

        self._insert_user = self.db.prepare('SELECT * FROM insert_user($1, $2, $3, $4)')
        self._insert_chat = self.db.prepare('INSERT INTO chats(chat_id, title, members_count) VALUES ($1, $2, $3)')
        self._insert_user_in_chat = self.db.prepare('SELECT * FROM insert_user_in_chat($1, $2, $3, $4)')
        self._insert_message = self.db.prepare('SELECT * FROM insert_message($1, $2, $3, $4, $5)')

        self._insert_bot = self.db.prepare('INSERT INTO bots(title, members_count) VALUES ($1, $2)')
        self._insert_user_in_bot = self.db.prepare('SELECT * FROM insert_user_in_bot($1, $2, $3)')

        self._insert_food_order = self.db.prepare('SELECT * FROM insert_food_order($1, $2, $3, $4, $5)')
        self._insert_bus_click = self.db.prepare('SELECT * FROM insert_bus_click($1, $2, $3, $4, $5)')
        self._insert_placed_ad = self.db.prepare('SELECT * FROM insert_placed_ad($1, $2, $3, $4, $5, $6)')

    def insert_user(self, user: User):
        self._insert_user(user.uid, user.first_name, user.last_name, user.username)

    def insert_chat(self, chat: Chat):
        self._insert_chat(chat.cid, chat.title, chat.members_count)

    def insert_users_in_chat(self, chat: Chat):
        for uid in chat.users_ids:
            self._insert_user_in_chat(chat.cid, uid, None, None)

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

        # insert users
        users = entities.users
        for u in users:
            try:
                self.insert_user(u)
            except Exception as e:
                print(e)

        # insert chats
        chats = entities.chats
        for c in chats:
            try:
                self.insert_chat(c)
            except Exception as e:
                print(e)
            try:
                self.insert_users_in_chat(c)
            except Exception as e:
                print(e)

        # insert messages
        messages = entities.messages
        for m in messages:
            try:
                self.insert_message(m)
            except Exception as e:
                print(e)
