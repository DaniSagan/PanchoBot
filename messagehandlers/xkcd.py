import random
from typing import List

import utils
from bot import MessageHandlerBase, BotBase
from data import Message, ChatState


class Xkcd(MessageHandlerBase):

    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None):
        words = message.text.split(' ')  # type: List[str]
        if words[0].lower() == 'xkcd':
            if len(words) == 1:
                bot.send_message(message.chat, self.get_image_url(self.get_latest_id()))
            elif words[1].lower() == 'random':
                num = random.randint(1, self.get_latest_id())  # type: int
                bot.send_message(message.chat, self.get_image_url(num))

    def get_latest_id(self) -> int:
        url = 'https://xkcd.com/info.0.json'  # type: str
        json_obj = utils.get_url_json(url)  # type: Dict
        return json_obj['num']

    def get_image_url(self, num: int) -> str:
        url = 'https://xkcd.com/{n}/info.0.json'.format(n=str(num))  # type: str
        json_obj = utils.get_url_json(url)  # type: Dict
        return json_obj['img']
