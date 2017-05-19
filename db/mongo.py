from typing import Set, List, Any

from bson import ObjectId
from pymongo.database import Database

from models import UserInBot, Bot, FoodOrder
from pymongo import MongoClient

# Mongo settings
mongo_host = 'localhost'
mongo_port = 27017
mongo_db_name = 'foodservice'

# Mapping of bots' names to databases in Mongo
bots_names_dbs = {
        'InnoHelpBot': 'shuttles',
        'InnoAdsBot': 'innoads',
        'GeekCaffeeBot': 'matcha',
        'InnoEdaBot': 'provip'
}

# Names of the DBs in which the data from a FoodBot are stored
food_bots_dbs_names = ["matcha", "provip"]


class MongoDB(object):
    _sessions_collection = 'sessions'

    def __init__(self):
        self.mongo_client = MongoClient(mongo_host, int(mongo_port))    # .get_database(db_name)

    def get_bots(self) -> Set[Bot]:
        """
        Returns set of all the available bots.
        Bots names and corresponding names of databases must be specified in :bots_names_dbs
        :param bots_names_dbs: {BOT_NAME: DB_NAME, ...}
        :return: set of Bot entities
        """
        bots = set()

        for bot_name, db_name in bots_names_dbs.items():
            db = self.mongo_client.get_database(db_name)
            bot_sessions = db.get_collection(self._sessions_collection).find()

            bots.add(Bot(bot_name, bot_sessions.count()))

        return bots

    def get_users_in_bots(self) -> Set[UserInBot]:
        users_in_bots = set()

        for bot_name, db_name in bots_names_dbs.items():
            db = self.mongo_client.get_database(db_name)
            bot_sessions = db.get_collection(self._sessions_collection).find()

            # parse set of the users in bot
            bot_users = set(UserInBot(bot_name, s.get('chat_id'), s.get('lang')) for s in list(bot_sessions))

            users_in_bots.update(bot_users)

        return users_in_bots

    def get_food_orders(self) -> Set[FoodOrder]:
        orders = set()

        for db_name in food_bots_dbs_names:
            db = self.mongo_client.get_database(db_name)
            orders.update(self._parse_food_orders(db))

        return orders

    @classmethod
    def _parse_food_orders(cls, db: Database) -> Set[FoodOrder]:
        _orders_collection = 'orders'

        food_orders = set()

        orders_cursor = db.get_collection(_orders_collection).find()

        for order in orders_cursor:
            user_id = order.get('author_chat_id')                       # get id of the user ordered
            timestamp = order.get('updates', {}).get('created_at')      # get timestamp of the order

            cart = order.get('cart', [])

            for item in cart:
                item_id = item.get('item_id')
                
                if item_id:
                    # get item's quantity
                    quantity = item.get('quantity')

                    # get food item title and category
                    item_title, item_category = cls._get_category_and_item(db, item_id)

                    # add new food order
                    food_orders.add(FoodOrder(user_id, item_category, item_title, quantity, timestamp))

                else:
                    print('Missing item_id parameter')

        return food_orders

    @classmethod
    def _get_category_and_item(cls, db: Database, item_id: Any) -> (str, str):
        """
        Retrieves item title and its category title for the item with the given item_id in the given db
        :return: (item_title, item_category_title)
        """
        _items_collection = 'items'
        _items_categories_collection = 'items_categories'

        # retrieve item object
        item_object = db.get_collection(_items_collection).find_one({"_id": ObjectId(item_id)})
        if not item_object:
            return None, None

        # get item title
        item_title = item_object.get('title', {}).get('ru')

        # retrieve category object
        category_object = db.get_collection(_items_categories_collection).find_one({
            "_id": item_object.get('category_id')
        })
        if not category_object:
            return item_title, None

        # get category title
        category_title = category_object.get('title', {}).get('ru')

        return item_title, category_title
