import sched
import threading

import time

import datetime
from sched import scheduler
from threading import Thread

from bot.base import MessageHandlerBase, BotBase
from data import Message, ChatState, Schedule
from data import Task
from textformatting import TextFormatter, MessageStyle
from wordparser import WordParser, MatchResult


class RemindData(object):
    def __init__(self):
        self.message: str = ''
        self.request_time: float = 0.


class ReminderMessageHandler(MessageHandlerBase):
    @staticmethod
    def get_help() -> TextFormatter:
        res: TextFormatter = TextFormatter()
        res.italic('\U00002328 Remind <interval> <message>').new_line().normal('Set a reminder for <interval> time.').new_line().new_line()
        res.normal('Examples:').new_line()
        res.italic('Remind 5m Turn off oven.').new_line()
        res.italic('Remind 1h30m Do homework.').new_line()
        return res

    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None) -> None:
        wp: WordParser = WordParser.from_str('cmd:w interval:t msg:*w')
        parse_res: MatchResult = wp.match(message.text)
        if parse_res.success:
            if parse_res.results['cmd'].lower() == 'remind':
                s: scheduler = sched.scheduler(time.time, time.sleep)
                data: RemindData = RemindData()
                data.message = ' '.join(parse_res.results['msg'])
                data.request_time = time.time()
                s.enter(parse_res.results['interval'], 1, self.action, (message, bot, data))
                t: Thread = threading.Thread(target=s.run)
                t.start()
                bot.send_message(message.chat, 'Done', MessageStyle.NONE)
            if parse_res.results['cmd'].lower() == 'testremind':
                task: Task = Task()
                task.chat = message.chat
                schedule: Schedule = Schedule()
                schedule.start = time.time() + 60
                schedule.end = time.time() + 120
                schedule.interval_seconds = 10
                task.schedule = schedule
                bot.scheduler.add_task(task)
                bot.send_message(message.chat, 'Task was set', MessageStyle.NONE)

    def action(self, message: Message, bot: BotBase, data: RemindData) -> None:
        rt: str = datetime.datetime.fromtimestamp(data.request_time).strftime('%Y-%m-%d %H:%M:%S')
        msg: TextFormatter = TextFormatter.instance().bold(f'You told me to remind you on {rt}:\n').normal(data.message)
        bot.send_message(message.chat, msg, MessageStyle.MARKDOWN)
