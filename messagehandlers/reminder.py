import sched
import threading

import time

import datetime

from bot import MessageHandlerBase, BotBase
from data import Message, ChatState
from textformatting import TextFormatter, MessageStyle
from wordparser import WordParser


class RemindData(object):
    def __init__(self):
        self.message = ''  # type: str
        self.request_time = 0.  # type: float


class ReminderHandler(MessageHandlerBase):
    @staticmethod
    def get_help() -> TextFormatter:
        res = TextFormatter()
        res.italic('\U00002328 Remind <interval> <message>').new_line().normal('Set a reminder for <interval> time.').new_line().new_line()
        res.normal('Examples:').new_line()
        res.italic('Remind 5m Turn off oven.').new_line()
        res.italic('Remind 1h30m Do homework.').new_line()
        return res

    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None) -> None:
        wp = WordParser.from_str('cmd:w interval:t msg:*w')
        parse_res = wp.match(message.text)
        if parse_res.success:
            if parse_res.results['cmd'].lower() == 'remind':
                s = sched.scheduler(time.time, time.sleep)
                data = RemindData()
                data.message = ' '.join(parse_res.results['msg'])
                data.request_time = time.time()
                s.enter(parse_res.results['interval'], 1, self.action, (message, bot, data))
                t = threading.Thread(target=s.run)
                t.start()
                bot.send_message(message.chat, 'Done', MessageStyle.NONE)

    def action(self, message: Message, bot: BotBase, data: RemindData) -> None:
        rt = datetime.datetime.fromtimestamp(data.request_time).strftime('%Y-%m-%d %H:%M:%S')  # type: str
        msg = TextFormatter.instance().bold('You told me to remind you on {d}:\n'.format(d=rt)).normal(data.message)  # type: str
        bot.send_message(message.chat, msg, MessageStyle.MARKDOWN)
