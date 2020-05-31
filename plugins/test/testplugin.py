from bot.base import BotBase
from bot.plugins import Plugin
from textformatting import MessageStyle


class TestPlugin(Plugin):
    def on_load(self, bot: BotBase) -> None:
        bot.broadcast('Test plugin loaded!!!!!!!!!!!!!!!', MessageStyle.NONE)
