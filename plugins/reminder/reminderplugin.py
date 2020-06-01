from bot.base import BotBase
from bot.plugins import Plugin
from plugins.reminder.reminder import ReminderMessageHandler


class ReminderPlugin(Plugin):
    def on_load(self, bot: BotBase) -> None:
        bot.add_message_handler('reminder', ReminderMessageHandler)