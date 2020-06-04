from bot.base import BotBase
from bot.plugins import Plugin
from plugins.messagesender.messagesender import MesageSenderMessageHandler


class MessageSenderPlugin(Plugin):
    def name(self) -> str:
        return 'messagesender'

    def on_load(self, bot: BotBase) -> None:
        bot.add_message_handler('messagesender', MesageSenderMessageHandler)