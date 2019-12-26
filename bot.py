import http.client
from enum import Enum
from typing import List

import utils
from data import GetUpdatesResponse, Chat, Message, BotConfig, ChatState, CallbackQuery
from db.database import Database, DataSet, DataRow, DataTable
import json
from typing import Dict, Optional
import urllib.request
import urllib.parse


class InlineKeyboardButton(object):
    def __init__(self):
        self.text = ''  # type: str
        self.url = ''  # type: str
        self.callback_data = ''  # type: str

    def to_json(self) -> Dict:
        if self.url and not self.callback_data:
            return {'text': self.text, 'url': self.url}
        elif not self.url and self.callback_data:
            return {'text': self.text, 'callback_data': self.callback_data}


class InlineKeyboardMarkup(object):
    def __init__(self):
        self.inline_keyboard = []  # type: List[List[InlineKeyboardButton]]

    @staticmethod
    def from_str_list(str_list: List[str]) -> 'InlineKeyboardMarkup':
        res = InlineKeyboardMarkup()
        res.inline_keyboard.append([])
        for s in str_list:
            button = InlineKeyboardButton()
            button.text = s
            button.callback_data = s
            res.inline_keyboard[0].append(button)
        return res

    def to_json(self) -> Dict:
        return {'inline_keyboard': [[button.to_json() for button in row] for row in self.inline_keyboard]}


class MessageStyle(Enum):
    NONE = 0
    MARKDOWN = 1
    HTML = 2


class BotBase(object):

    def __init__(self):
        self.database = None  # type: Database
        self.running = True

    def get_updates(self) -> GetUpdatesResponse:
        raise NotImplementedError()

    def send_message(self, chat: Chat, text: str, style: MessageStyle) -> Message:
        raise NotImplementedError()

    def send_message_with_inline_keyboard(self, chat: Chat, text: str, style: MessageStyle, inline_keyboard: InlineKeyboardMarkup) -> Message:
        raise NotImplementedError()

    def answer_callback_query(self, callback_query_id: str) -> bool:
        raise NotImplementedError()

    def stop(self):
        self.running = False


class MessageHandlerBase(object):
    def __init__(self):
        self.handler_name = ''  # type: str

    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None):
        raise NotImplementedError()

    def process_callback_query(self, callback_query: CallbackQuery, bot: BotBase, chat_state: ChatState = None):
        bot.send_message(callback_query.message.chat, 'process_callback_query not defined for handler ' + self.handler_name, MessageStyle.NONE)

    @staticmethod
    def get_help() -> str:
        return 'Help message not defined.'


class Bot(BotBase):

    def __init__(self, token: str, config: BotConfig):
        BotBase.__init__(self)
        self.token = token  # type: str
        self.config = config  # type: BotConfig
        self.message_handlers = {}  # type: Dict[str, type]

    def initialize(self):
        with open(self.config.database_definition_file) as fobj:
            db_definition_str = fobj.read()  # type: str
        self.database = Database.from_json(json.loads(db_definition_str))
        self.database.create_tables()

    def run(self):
        while self.running:
            print('Waiting for messages...')
            response = self.get_updates()  # type: GetUpdatesResponse
            for update in response.result:
                if update.message is not None:
                    self.on_new_message(update.message)
                if update.callback_query is not None:
                    self.on_new_callback_query(update.callback_query)
        print('Stopped')

    def base_url(self) -> str:
        return 'https://api.telegram.org/bot{t}/'.format(t=self.token)

    def call(self, action: str, params: Dict = None) -> Dict:
        if params is not None:
            req = urllib.request.Request(self.base_url() + action, urllib.parse.urlencode(utils.dict_to_url_params(params)).encode('ascii'))
        else:
            req = urllib.request.Request(self.base_url() + action)
        with urllib.request.urlopen(req) as response:  # type:  http.client.HTTPResponse
            if response.status == 200:
                received_bytes = response.read()  # type: bytes
                received_str = received_bytes.decode("utf8")  # type: str
            else:
                raise RuntimeError('Could not execute action {a}. Reason: {r}'.format(a=action, r=response.reason))

        # noinspection PyUnboundLocalVariable
        print('Received response: {r}'.format(r=received_str))
        return json.loads(received_str)

    def get_updates(self) -> GetUpdatesResponse:

        last_update_id = self.get_last_update_id()  # type: Optional[int]
        if last_update_id is None:
            json_resp = self.call('getUpdates', {"timeout": self.config.get_updates_timeout})
        else:
            json_resp = self.call('getUpdates', {"timeout": self.config.get_updates_timeout, "offset": last_update_id+1})
        res = GetUpdatesResponse.from_json(json_resp)

        if len(res.result) == 0:
            return res

        ds = DataSet()  # type: DataSet
        for result in res.result:
            ds.merge(result.to_data_set())

        last_update_id = max(r.id_update for r in res.result)  # type: int
        last_update_id_row = DataRow('parameter', 'last_update_id')
        last_update_id_row.put('key', 'last_update_id')
        last_update_id_row.put('value', str(last_update_id))
        ds.merge_row(last_update_id_row)

        connection = self.database.create_connection()
        self.database.save_data_set(connection, ds)
        connection.commit()

        return res

    def send_message(self, chat: Chat, text: str, style: MessageStyle) -> Message:
        message_params = {'chat_id': chat.id_chat, 'text': text}
        resp = self.call('sendMessage', message_params)
        sent_message = Message.from_json(resp['result'])
        self.database.save(sent_message)
        return sent_message

    def send_message_with_inline_keyboard(self, chat: Chat, text: str, style: MessageStyle, inline_keyboard: InlineKeyboardMarkup) -> Message:
        message_params = {'chat_id': chat.id_chat, 'text': text, 'reply_markup': inline_keyboard.to_json()}
        resp = self.call('sendMessage', message_params)
        sent_message = Message.from_json(resp['result'])
        self.database.save(sent_message)
        return sent_message

    def answer_callback_query(self, callback_query_id: str):
        self.call('answerCallbackQuery', {'callback_query_id': callback_query_id, 'text': 'Hello', 'show_alert': False})

    def get_last_update_id(self) -> Optional[int]:
        connection = self.database.create_connection()
        dt = self.database.query(connection, 'parameter', 'last_update_id', False)  # type: DataTable
        if len(dt.rows) > 0:
            return int(list(dt.rows.values())[0].get('value'))
        else:
            return None

    def on_new_message(self, message: Message):
        chat_state = message.chat.retrieve_chat_state()
        if message.text.lower() == 'status':
            if chat_state is not None:
                self.send_message(message.chat, 'Current handler: {h}'.format(h=chat_state.current_handler_name), MessageStyle.NONE)
            else:
                self.send_message(message.chat, 'OK', MessageStyle.NONE)
        elif message.text.lower() == 'quit':
            message.chat.remove_chat_state()
        elif message.text.lower() == 'help':
            if chat_state is None:
                help_msgs = []
                for handler_name in self.message_handlers:
                    help_msgs.append(handler_name + ':\n' + self.message_handlers[handler_name].get_help())
                self.send_message(message.chat, '\n\n'.join(help_msgs), MessageStyle.NONE)
            else:
                help_msg = self.message_handlers[chat_state.current_handler_name].get_help()
                self.send_message(message.chat, chat_state.current_handler_name + ':\n' + help_msg, MessageStyle.NONE)
        else:
            if chat_state is not None:
                instance = self.message_handlers[chat_state.current_handler_name]()
                instance.handler_name = chat_state.current_handler_name
                try:
                    instance.process_message(message, self, chat_state)
                except Exception as ex:
                    self.send_message(message.chat, 'Error: {e}'.format(e=str(ex)), MessageStyle.NONE)
            for handler_name in self.message_handlers:
                instance = self.message_handlers[handler_name]()
                instance.handler_name = handler_name
                try:
                    instance.process_message(message, self)
                except Exception as ex:
                    self.send_message(message.chat, 'Error: {e}'.format(e=str(ex)), MessageStyle.NONE)

    def on_new_callback_query(self, callback_query: CallbackQuery):
        chat_state = callback_query.message.chat.retrieve_chat_state()
        if chat_state is not None:
            instance = self.message_handlers[chat_state.current_handler_name]()
            instance.handler_name = chat_state.current_handler_name
            try:
                instance.process_callback_query(callback_query, self, chat_state)
            except Exception as ex:
                self.send_message(callback_query.message.chat, 'Error: {e}'.format(e=str(ex)), MessageStyle.NONE)
        else:
            self.send_message(callback_query.message.chat, 'Could not retrieve chat state', MessageStyle.NONE)
