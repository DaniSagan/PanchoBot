from bot.base import BotBase
from bot.plugins import Plugin


class SchedulerTestPlugin(Plugin):
    def on_load(self, bot: BotBase) -> None:
        bot.scheduler.add_task()

    def name(self) -> str:
        return "scheduler test"
