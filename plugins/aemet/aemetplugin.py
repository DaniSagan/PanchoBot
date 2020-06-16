from typing import Dict

import logging

import time

import utils
from bot.base import BotBase, MessageHandlerBase
from bot.plugins import Plugin
from data import ChatState, Message
from jsonutils import JsonDeserializable
from textformatting import MessageStyle
from wordparser import WordParser, MatchResult


class AemetResponse(JsonDeserializable):
    def __init__(self):
        self.description: str or None = None
        self.state: int = 0
        self.data: str or None = None
        self.metadata: str or None = None

    @classmethod
    def from_json(cls, json_object: Dict) -> 'AemetResponse':
        res: AemetResponse = AemetResponse()
        res.description = json_object['descripcion']
        res.state = json_object['estado']
        res.data = json_object.get('datos')
        res.metadata = json_object.get('metadatos')
        return res


class AemetMessageHandler(MessageHandlerBase):
    BASE_URL: str = 'https://opendata.aemet.es/opendata/api'

    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None):
        wp: WordParser = WordParser.from_str('cmd:w')
        parse_res: MatchResult = wp.match(message.text)
        if parse_res.success:
            if parse_res.results['cmd'].lower() == 'tiempo':
                res: AemetResponse = self.get_radar_regional(bot.tokens['aemet'], 'sa')
                logging.debug(res)
                bot.send_message(message.chat, f'{res.data}?a={time.time()}', MessageStyle.NONE)

    def get_radar_regional(self, token: str, region: str) -> AemetResponse:
        return AemetResponse.load_from_json_url(f'{self.BASE_URL}/red/radar/regional/{region}?api_key={token}')


class AemetPlugin(Plugin):
    def on_load(self, bot: BotBase) -> None:
        bot.add_message_handler('aemet', AemetMessageHandler)
        token: str = utils.get_file_json('plugins/aemet/tokens.json')['aemet']
        bot.tokens['aemet'] = token

    def name(self) -> str:
        return 'aemet'