from bot.base import BotBase
from bot.plugins import Plugin
from plugins.tua.tua import TuaMessageHandler


class TuaPlugin(Plugin):
    def name(self) -> str:
        return 'tua'

    def on_load(self, bot: BotBase) -> None:
        bot.add_message_handler('tua', TuaMessageHandler)
