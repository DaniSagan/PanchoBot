from bot.base import BotBase
from bot.plugins import Plugin
from plugins.oeis.oeis import OeisMessageHandler


class OeisPlugin(Plugin):
    def name(self) -> str:
        return 'oeis'

    def on_load(self, bot: BotBase) -> None:
        bot.add_message_handler('oeis', OeisMessageHandler)