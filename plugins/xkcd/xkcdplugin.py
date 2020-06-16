import random
from typing import Dict
from typing import List

import utils
from bot.base import BotBase, MessageHandlerBase
from bot.plugins import Plugin
from data import Message, ChatState
from textformatting import MessageStyle


class XkcdPlugin(Plugin):
    def name(self) -> str:
        return 'xkcd'

    def on_load(self, bot: BotBase) -> None:
        bot.add_message_handler('xkcd', XkcdMessageHandler)


class XkcdMessageHandler(MessageHandlerBase):

    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None):
        words: List[str] = message.text.split(' ')
        if words[0].lower() == 'xkcd':
            if len(words) == 1:
                bot.send_message(message.chat, self.get_image_url(self.get_latest_id()), MessageStyle.NONE)
            elif words[1].lower() == 'random':
                num: int = random.randint(1, self.get_latest_id())
                bot.send_message(message.chat, self.get_image_url(num), MessageStyle.NONE)

    def get_latest_id(self) -> int:
        url: str = 'https://xkcd.com/info.0.json'
        json_obj: Dict = utils.get_url_json(url)
        return json_obj['num']

    def get_image_url(self, num: int) -> str:
        url: str = f'https://xkcd.com/{str(num)}/info.0.json'
        json_obj: Dict = utils.get_url_json(url)
        return json_obj['img']
