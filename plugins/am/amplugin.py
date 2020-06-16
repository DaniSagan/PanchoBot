from typing import List

import utils
from bot.base import BotBase, MessageHandlerBase
from bot.plugins import Plugin
from data import Message, ChatState
from textformatting import MessageStyle, TextFormatter
from wordparser import MatchResult
from wordparser import WordParser


def interval_to_journeys(interval: float) -> float:
    return round(interval / 3600 * 5 / 39, 2)


class AmMessageHandler(MessageHandlerBase):
    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None):
        wp: WordParser = WordParser.from_str('cmd:w interval:*t')
        parse_res: MatchResult = wp.match(message.text)
        if parse_res.success:
            if parse_res.results['cmd'].lower() == 'chp':
                intervals: List[str] = parse_res.results['interval']
                if intervals:
                    bot.send_message(message.chat, str(sum(map(interval_to_journeys, intervals))), MessageStyle.NONE)
                else:
                    tf: TextFormatter = TextFormatter.instance()
                    total_minutes: int = 15
                    while total_minutes <= 9*60:
                        hours: int = total_minutes // 60
                        minutes: int = total_minutes % 60
                        if hours > 0:
                            tf.bold(str(hours)+'h')
                        if minutes > 0:
                            tf.bold(str(minutes)+'m')
                        tf.bold(': ').normal(str(interval_to_journeys(total_minutes*60)) + ' jornadas')
                        if minutes == 45:
                            tf.new_line().normal('\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_')
                        tf.new_line()
                        total_minutes += 15
                    bot.send_message(message.chat, tf, MessageStyle.MARKDOWN)


class AmPlugin(Plugin):
    def name(self) -> str:
        return 'am'

    def on_load(self, bot: BotBase) -> None:
        bot.add_message_handler('am', AmMessageHandler)
