import random
from typing import Dict
from typing import List

import utils
from bot.base import BotBase, MessageHandlerBase
from bot.plugins import Plugin
from data import Message, ChatState
from textformatting import MessageStyle


class XkcdPlugin(Plugin):
    def on_load(self, bot: BotBase) -> None:
        bot.add_message_handler('xkcd', XkcdMessageHandler)


class XkcdMessageHandler(MessageHandlerBase):

    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None):
        words = message.text.split(' ')  # type: List[str]
        if words[0].lower() == 'xkcd':
            if len(words) == 1:
                bot.send_message(message.chat, self.get_image_url(self.get_latest_id()), MessageStyle.NONE)
            elif words[1].lower() == 'random':
                num = random.randint(1, self.get_latest_id())  # type: int
                bot.send_message(message.chat, self.get_image_url(num), MessageStyle.NONE)

    def get_latest_id(self) -> int:
        url = 'https://xkcd.com/info.0.json'  # type: str
        json_obj = utils.get_url_json(url)  # type: Dict
        return json_obj['num']

    def get_image_url(self, num: int) -> str:
        url = 'https://xkcd.com/{n}/info.0.json'.format(n=str(num))  # type: str
        json_obj = utils.get_url_json(url)  # type: Dict
        return json_obj['img']
