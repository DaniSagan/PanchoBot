import argparse
import logging
import ssl
import sys

import data
from bot.bot import Bot
from data import BotConfig
from db.database import Database
from objectprovider import ObjectProvider

if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                        level=logging.DEBUG,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        stream=sys.stdout)

    parser = argparse.ArgumentParser()
    parser.add_argument('--no-ssl-cert', action='store_true')
    args = parser.parse_args()

    if args.no_ssl_cert:
        ssl._create_default_https_context = ssl._create_unverified_context

    bot_config = data.BotConfig.load_from_json_file('bot_config.json')  # type: BotConfig
    database = Database.load_from_json_file(bot_config.database_definition_file)  # type: Database
    database.create_tables()
    object_provider = ObjectProvider.load_from_json_file('op_definition.json')  # type: ObjectProvider

    pancho_bot = Bot(bot_config, object_provider, database)  # type: Bot
    pancho_bot.initialize()
    pancho_bot.run()
