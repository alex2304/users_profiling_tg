import os


class Settings:
    # path to the file with target chats titles
    target_chats_file_path = os.path.join(os.path.dirname(__file__), 'raw_data/target_chats')
    tg_config_file_path = os.path.join(os.path.dirname(__file__), 'raw_data/tg_config')

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
