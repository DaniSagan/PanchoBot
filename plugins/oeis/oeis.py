import random
from typing import Dict, List
from typing import List

import utils
from bot.base import MessageHandlerBase, BotBase
from data import Message, ChatState
from jsonutils import JsonDeserializable
from textformatting import TextFormatter, MessageStyle


class QueryResultItem(JsonDeserializable):
    def __init__(self):
        self.number: int = 0
        self.data: str = ''
        self.name: str = ''

    @classmethod
    def from_json(cls, json_object: Dict) -> 'QueryResultItem':
        res: QueryResultItem = QueryResultItem()
        res.number = json_object['number']
        res.data = json_object['data']
        res.name = json_object['name']
        return res


class QueryResult(JsonDeserializable):
    def __init__(self):
        self.greeting: str = ''
        self.query: str = ''
        self.count: int = 0
        self.start: int = 0
        self.results: List[QueryResultItem] = []

    @classmethod
    def from_json(cls, json_object: Dict) -> 'QueryResult':
        res: QueryResult = QueryResult()
        res.greeting = json_object['greeting']
        res.query = json_object['query']
        res.count = json_object['count']
        res.start = json_object['start']
        res.results = [QueryResultItem.from_json(j) for j in json_object['results']]
        return res


class OeisMessageHandler(MessageHandlerBase):
    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None):
        words: List[str] = message.text.split(' ')
        if words[0].lower() == 'oeis':
            query = 'keyword:look'
            start = 0
            json_obj = utils.get_url_json(f'https://oeis.org/search?fmt=json&q={query}&start={start}')
            result: QueryResult = QueryResult.from_json(json_obj)
            count: int = result.count
            random_num = random.randint(1, count)
            json_obj = utils.get_url_json(f'https://oeis.org/search?fmt=json&q={query}&start={random_num}')
            result = QueryResult.from_json(json_obj)
            img_url = f'https://oeis.org/A{result.results[0].number:06}/graph?png=1'
            bot.send_message(message.chat,
                             TextFormatter.instance().inline_code(result.results[0].name),
                             MessageStyle.MARKDOWN)
            bot.send_message(message.chat, img_url, MessageStyle.NONE)
