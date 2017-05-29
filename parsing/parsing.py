import json
import os
import re
from datetime import datetime
from typing import Set, List, Any
from bson import ObjectId
from pymongo.database import Database
from pymongo import MongoClient

from models import UserInBot, Bot, FoodOrder, BusClick, PlacedAd


class Settings:
    # Mongo settings to connect
    mongo_host = 'localhost'
    mongo_port = 27017

    # Mapping of bots' names to databases in Mongo
    bots_names_dbs = {
        'InnoHelpBot': 'shuttles',
        'InnoAdsBot': 'innoads',
        'GeekCaffeeBot': 'matcha',
        'InnoEdaBot': 'provip'
    }

    # Names of the DBs in which the data from a FoodBot are stored
    food_bots_dbs_names = [bots_names_dbs.get('GeekCaffeeBot'), bots_names_dbs.get('InnoEdaBot')]

    # Name of the DB with shuttles data
    shuttles_db_name = bots_names_dbs.get('InnoHelpBot')
    shuttles_clicks_filename = os.path.join(os.path.dirname(__file__), 'raw_data/innohelp_clicks.txt')

    # Name of the DB with ads data
    ads_db_name = bots_names_dbs.get('InnoAdsBot')


class DataParser:
    _sessions_collection = 'sessions'

    def __init__(self):
        self.mongo_client = MongoClient(Settings.mongo_host, int(Settings.mongo_port))

    def get_bots(self) -> Set[Bot]:
        """
        Scans all the databases, specified in Settings.bots_names_dbs.
        :return: set of all the available bots
        """
        bots = set()

        for bot_name, db_name in Settings.bots_names_dbs.items():
            db = self.mongo_client.get_database(db_name)
            bot_sessions = db.get_collection(self._sessions_collection).find()

            bots.add(Bot(bot_name, bot_sessions.count()))

        return bots

    def get_users_in_bots(self) -> Set[UserInBot]:
        """
        Scans all the databases, specified in Settings.bots_names_dbs.
        :return: set of all the users in all the available bots
        """
        users_in_bots = set()

        for bot_name, db_name in Settings.bots_names_dbs.items():
            db = self.mongo_client.get_database(db_name)
            bot_sessions = db.get_collection(self._sessions_collection).find()

            # parse set of the users in bot
            bot_users = set(UserInBot(bot_name, s.get('chat_id'), s.get('lang')) for s in list(bot_sessions))

            users_in_bots.update(bot_users)

        return users_in_bots

    def get_food_orders(self) -> Set[FoodOrder]:
        """
        Scans databases of food bots, specified in Settings.food_bots_dbs_names.
        :return: all the food orders gathered from available DBs
        """
        orders = set()

        for db_name in Settings.food_bots_dbs_names:
            db = self.mongo_client.get_database(db_name)
            orders.update(self._parse_food_orders(db))

        return orders

    @classmethod
    def _parse_food_orders(cls, db: Database) -> Set[FoodOrder]:
        _orders_collection = 'orders'

        food_orders = set()

        orders_cursor = db.get_collection(_orders_collection).find()

        for order in orders_cursor:
            user_id = order.get('author_chat_id')
            timestamp = order.get('updates', {}).get('created_at')

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

    def get_bus_clicks(self) -> Set[BusClick]:
        """
        Reads file with shuttle clicks data (filename is specified at Settings.shuttles_clicks_filename)
        :return: all the bus clicks gathered from the file
        """
        click_timestamp_format = '%Y-%m-%d %H:%M:%S.%f'
        bus_clicks = set()

        # retrieve information about routes from the DB
        daily_routes_info = self._retrieve_routes_information()

        # process each click action
        shuttle_clicks = self._read_shuttle_clicks(Settings.shuttles_clicks_filename)
        for click_action in shuttle_clicks:
            shuttle_id = int(click_action.get('new_value'))
            user_id = json.loads(click_action.get('filter_options', '{}').replace('\'', '\"')).get('chat_id')
            click_timestamp = datetime.strptime(click_action.get('dt'), click_timestamp_format)

            click_date = click_action.get('dt').split(' ')[0].replace('-', '/')
            # get click date for searching in db
            try:
                route_id, route_start_timestamp = self._get_route_info(shuttle_id, click_date, daily_routes_info)

            except ValueError:
                print('Missed for (date, shuttle_id): %s %s' % (click_date, shuttle_id))

            else:
                # add new bus click
                bus_clicks.add(BusClick(user_id, click_timestamp, route_id, shuttle_id, route_start_timestamp))

        return bus_clicks

    def _retrieve_routes_information(self) -> List[dict]:
        # retrieve from the DB information about routes at different days
        _routes_collection = 'schedule'

        # get information (shuttle id and "route" field) about all the dates
        shuttles_db = self.mongo_client.get_database(Settings.shuttles_db_name)
        daily_routes = shuttles_db.get_collection(_routes_collection).find({})

        return [day_route for day_route in daily_routes]

    @staticmethod
    def _read_shuttle_clicks(file_path: str):
        shuttle_click_pattern = re.compile('.*(key = wanted_shuttle_id).*')
        with open(file_path, 'r') as f:
            shuttle_clicks = []

            for line in f:
                if re.match(shuttle_click_pattern, line):
                    action = dict([tuple(field.split(' = ')) for field in line.split(' | ')])
                    shuttle_clicks.append(action)

            return shuttle_clicks

    @staticmethod
    def _get_route_info(shuttle_id: int, date_day: str, daily_routes) -> (str, datetime):
        """
        Returns information about route of the given shuttle at the given day
        :return: (route_id: str, route_start_time: datetime)
        """
        _timestamp_template = '%Y/%m/%d %H:%M'

        # find corresponding date_day
        wanted_day_routes = None
        for routes_at_day in daily_routes:
            # if there is a wanted day
            if routes_at_day.get(date_day):
                wanted_day_routes = routes_at_day.get(date_day)
                break

        if wanted_day_routes:
            for single_route_data in wanted_day_routes:
                if single_route_data.get('shuttle_id') == shuttle_id:
                    start_time = single_route_data.get('time')
                    start_timestamp = datetime.strptime('%s %s' % (date_day, start_time), _timestamp_template)

                    route_id = single_route_data.get('route', {}).get('id')

                    return route_id, start_timestamp

        raise ValueError('Unknown day or shuttle id')

    def get_placed_ads(self) -> List[PlacedAd]:
        """
        Scans database specified in Settings.ads_db_name
        :return: all the placed ads gathered from the ads database
        """
        _ads_collection = 'data'
        _placed_timestamp_format = '%H:%M %d.%m.%Y'
        placed_ads = set()

        ads_collection = self.mongo_client.get_database(Settings.ads_db_name).get_collection(_ads_collection)
        ads_categories = ads_collection.find_one().get('stories')

        for category in ads_categories:
            category_title = category.get('section_name')
            category_content = category.get('content')

            for cat_type_title, cat_type_content in category_content.items():
                for ad in cat_type_content:
                    user_id = ad.get('author_id')
                    likes_count = ad.get('likes')
                    views_count = ad.get('views', {}).get('count')
                    placed_timestamp = datetime.strptime(ad.get('datetime'), _placed_timestamp_format)

                    placed_ads.add(PlacedAd(user_id, placed_timestamp, category_title, cat_type_title,
                                            views_count, likes_count))

        return placed_ads
