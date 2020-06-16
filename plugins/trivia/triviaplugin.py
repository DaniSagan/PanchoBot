from bot.base import BotBase
from bot.plugins import Plugin
from plugins.trivia.trivia import TriviaMessageHandler


class TriviaPlugin(Plugin):
    def name(self) -> str:
        return 'trivia'

    def on_load(self, bot: BotBase) -> None:
        bot.add_message_handler('trivia', TriviaMessageHandler)
