from bot.base import BotBase
from bot.plugins import Plugin
from plugins.terminal.terminal import PowerOff


class TerminalPlugin(Plugin):
    def on_load(self, bot: BotBase) -> None:
        bot.add_message_handler('terminal', PowerOff)
