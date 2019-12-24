import data
import json
import bot

import messagehandlers.messagesender
import messagehandlers.terminal

if __name__ == '__main__':
    with open('token.txt') as fobj:
        token = fobj.read().strip()
    with open('bot_config.json') as fobj:
        bot_config_json = json.loads(fobj.read().strip())
    pancho_bot = bot.Bot(token, data.BotConfig.from_json(bot_config_json))  # type: bot.Bot
    pancho_bot.initialize()
    pancho_bot.message_handlers.append(messagehandlers.messagesender.MessageSender())
    pancho_bot.message_handlers.append(messagehandlers.terminal.PowerOff())
    pancho_bot.run()
    # response = pancho_bot.get_updates()  # type: data.GetUpdatesResponse
    # sent_message = pancho_bot.send_message(response.result[0].message.chat, 'Hello World!')
