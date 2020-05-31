import argparse

import logging

import sys

import data
import json

import utils
from bot.bot import Bot
import ssl

import messagehandlers.messagesender
import messagehandlers.terminal
import messagehandlers.xkcd
import messagehandlers.exchangerates
import messagehandlers.trivia
import messagehandlers.newtoncalc
import messagehandlers.oeis
import messagehandlers.reminder
import messagehandlers.tua
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

    bot_config = data.BotConfig.from_json(utils.get_file_json('bot_config.json'))  # type: BotConfig
    database = Database.from_json(utils.get_file_json(bot_config.database_definition_file))  # type: Database
    database.create_tables()
    object_provider = ObjectProvider.load_from_json_file('op_definition.json')  # type: ObjectProvider

    pancho_bot = Bot(bot_config, object_provider, database)  # type: Bot
    pancho_bot.initialize()

    pancho_bot.message_handlers['sender'] = messagehandlers.messagesender.MessageSender
    pancho_bot.message_handlers['poweroff'] = messagehandlers.terminal.PowerOff
    pancho_bot.message_handlers['xkcd'] = messagehandlers.xkcd.Xkcd
    pancho_bot.message_handlers['exchangerates'] = messagehandlers.exchangerates.ExchangeRates
    pancho_bot.message_handlers['trivia'] = messagehandlers.trivia.Trivia
    pancho_bot.message_handlers['newton'] = messagehandlers.newtoncalc.NewtonCalc
    pancho_bot.message_handlers['oeis'] = messagehandlers.oeis.OeisHandler
    pancho_bot.message_handlers['remind'] = messagehandlers.reminder.ReminderHandler
    pancho_bot.message_handlers['tua'] = messagehandlers.tua.TuaHandler

    pancho_bot.run()
