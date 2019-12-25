import data
import json
import bot

import messagehandlers.messagesender
import messagehandlers.terminal
import messagehandlers.xkcd
import messagehandlers.exchangerates
import messagehandlers.trivia

if __name__ == '__main__':
    with open('token.txt') as fobj:
        token = fobj.read().strip()
    with open('bot_config.json') as fobj:
        bot_config_json = json.loads(fobj.read().strip())
    pancho_bot = bot.Bot(token, data.BotConfig.from_json(bot_config_json))  # type: bot.Bot
    pancho_bot.initialize()
    pancho_bot.message_handlers['sender'] = messagehandlers.messagesender.MessageSender
    pancho_bot.message_handlers['poweroff'] = messagehandlers.terminal.PowerOff
    pancho_bot.message_handlers['xkcd'] = messagehandlers.xkcd.Xkcd
    pancho_bot.message_handlers['exchangerates'] = messagehandlers.exchangerates.ExchangeRates
    pancho_bot.message_handlers['trivia'] = messagehandlers.trivia.Trivia
    pancho_bot.run()
    # response = pancho_bot.get_updates()  # type: data.GetUpdatesResponse
    # sent_message = pancho_bot.send_message(response.result[0].message.chat, 'Hello World!')
