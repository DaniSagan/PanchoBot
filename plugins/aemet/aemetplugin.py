from typing import Dict

import logging

import time

import utils
from bot.base import BotBase, MessageHandlerBase
from bot.plugins import Plugin
from data import ChatState, Message
from jsonutils import JsonDeserializable
from textformatting import MessageStyle
from wordparser import WordParser


class AemetResponse(JsonDeserializable):
    def __init__(self):
        self.description = None  # type: str
        self.state = 0  # type: int
        self.data = None  # type: str
        self.metadata = None  # type: str

    @classmethod
    def from_json(cls, json_object: Dict) -> 'AemetResponse':
        res = AemetResponse()
        res.description = json_object['descripcion']
        res.state = json_object['estado']
        res.data = json_object.get('datos')
        res.metadata = json_object.get('metadatos')
        return res


class AemetMessageHandler(MessageHandlerBase):
    BASE_URL = 'https://opendata.aemet.es/opendata/api'

    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None):
        wp = WordParser.from_str('cmd:w')
        parse_res = wp.match(message.text)
        if parse_res.success:
            if parse_res.results['cmd'].lower() == 'tiempo':
                res = self.get_radar_regional(bot.tokens['aemet'], 'sa')
                logging.debug(res)
                bot.send_message(message.chat, '{l}?a={d}'.format(l=res.data, d=time.time()), MessageStyle.NONE)

    def get_radar_regional(self, token: str, region: str) -> AemetResponse:
        return AemetResponse.load_from_json_url(
            self.BASE_URL + '/red/radar/regional/{r}?api_key={t}'.format(r=region, t=token))  # type: AemetResponse


class AemetPlugin(Plugin):
    def on_load(self, bot: BotBase) -> None:
        bot.add_message_handler('aemet', AemetMessageHandler)
        token = utils.get_file_json('plugins/aemet/tokens.json')['aemet']  # type: str
        bot.tokens['aemet'] = token

    def name(self) -> str:
        return 'aemet'