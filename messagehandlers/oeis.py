import random
from typing import Dict
from typing import List

import utils
from bot import MessageHandlerBase, BotBase, MessageStyle
from data import Message, ChatState
from jsonutils import JsonDeserializable
from textformatting import TextFormatter


class QueryResultItem(JsonDeserializable):
    def __init__(self):
        self.number = 0  # type: int
        self.data = ''  # type: str
        self.name = ''  # type: str

    @staticmethod
    def from_json(json_object: Dict) -> 'QueryResultItem':
        res = QueryResultItem()  # type: QueryResultItem
        res.number = json_object['number']
        res.data = json_object['data']
        res.name = json_object['name']
        return res


class QueryResult(JsonDeserializable):
    def __init__(self):
        self.greeting = ''  # type: str
        self.query = ''  # type: str
        self.count = 0  # type: int
        self.start = 0  # type: int
        self.results = []  # type: List[QueryResultItem]

    @staticmethod
    def from_json(json_object: Dict) -> 'QueryResult':
        res = QueryResult()  # type: QueryResult
        res.greeting = json_object['greeting']
        res.query = json_object['query']
        res.count = json_object['count']
        res.start = json_object['start']
        res.results = [QueryResultItem.from_json(j) for j in json_object['results']]  # type: List[QueryResultItem]
        return res


class OeisHandler(MessageHandlerBase):
    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None):
        words = message.text.split(' ')
        if words[0].lower() == 'oeis':
            query = 'keyword:look'
            start = 0
            json_obj = utils.get_url_json('https://oeis.org/search?fmt=json&q={q}&start={s}'.format(q=query, s=start))
            result = QueryResult.from_json(json_obj)  # type: QueryResult
            count = result.count
            random_num = random.randint(1, count)
            json_obj = utils.get_url_json('https://oeis.org/search?fmt=json&q={q}&start={s}'.format(q=query, s=random_num))
            result = QueryResult.from_json(json_obj)
            img_url = 'https://oeis.org/A{n:06}/graph?png=1'.format(n=result.results[0].number)
            bot.send_message(message.chat, TextFormatter.instance().inline_code(result.results[0].name), MessageStyle.MARKDOWN)
            bot.send_message(message.chat, img_url, MessageStyle.NONE)
