import utils
from bot.base import BotBase, MessageHandlerBase
from bot.plugins import Plugin
from data import Message, ChatState
from textformatting import MessageStyle
from wordparser import MatchResult
from wordparser import WordParser


class AmMessageHandler(MessageHandlerBase):
    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None):
        wp = WordParser.from_str('cmd:w interval:t')  # type: WordParser
        parse_res = wp.match(message.text)  # type: MatchResult
        if parse_res.success:
            if parse_res.results['cmd'].lower() == 'am':
                interval = parse_res.results['interval']  # type: float
                bot.send_message(message.chat, str(self.interval_to_journeys(interval)), MessageStyle.NONE)

    def interval_to_journeys(self, interval: float) -> float:
        return round(interval / 3600 * 5 / 39, 2)


class AmPlugin(Plugin):
    def name(self) -> str:
        return 'am'

    def on_load(self, bot: BotBase) -> None:
        bot.add_message_handler('am', AmMessageHandler)
