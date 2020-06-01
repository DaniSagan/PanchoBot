from bot.base import BotBase
from bot.plugins import Plugin
from plugins.tua.tua import TuaMessageHandler


class TuaPlugin(Plugin):
    def on_load(self, bot: BotBase) -> None:
        bot.add_message_handler('tua', TuaMessageHandler)
