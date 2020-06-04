from bot.base import BotBase
from bot.plugins import Plugin
from plugins.newtoncalc.newtoncalc import NewtonCalcMessageHandler


class NewtonCalcPlugin(Plugin):
    def name(self) -> str:
        return 'newtoncalc'

    def on_load(self, bot: BotBase) -> None:
        bot.add_message_handler('newtoncalc', NewtonCalcMessageHandler)