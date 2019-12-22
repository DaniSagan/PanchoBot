import data
import json

if __name__ == '__main__':
    with open('token.txt') as fobj:
        token = fobj.read().strip()
    with open('bot_config.json') as fobj:
        bot_config_json = json.loads(fobj.read().strip())
    bot = data.Bot(token, data.BotConfig.from_json(bot_config_json))  # type: Bot
    bot.initialize()
    print(bot.get_updates())
