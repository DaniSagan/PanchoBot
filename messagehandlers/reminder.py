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
