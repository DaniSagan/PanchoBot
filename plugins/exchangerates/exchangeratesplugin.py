from bot.base import BotBase
from bot.plugins import Plugin
from plugins.exchangerates.exchangerates import ExchangeRatesMessageHandler


class ExchangeRatesPlugin(Plugin):
    def on_load(self, bot: BotBase) -> None:
        bot.add_message_handler('exchangerates', ExchangeRatesMessageHandler)
