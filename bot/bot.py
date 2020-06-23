import http.client
import json
import logging
import socket
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from sqlite3.dbapi2 import Connection
from typing import Dict, Optional
from typing import List, Union

import utils
from bot.base import BotBase, InlineKeyboardMarkup, MessageHandlerBase
from bot.plugins import PluginCollection, Plugin
from data import GetUpdatesResponse, Chat, Message, BotConfig, ChatState, CallbackQuery, Task
from db.database import Database, DataSet, DataRow
from objectprovider import ObjectProvider
from scheduler import Scheduler
from scheduler import TaskExecutor
from textformatting import TextFormatter, MessageStyle


class Bot(BotBase, TaskExecutor):

    def __init__(self, config: BotConfig, object_provider: ObjectProvider, database: Database):
        BotBase.__init__(self)
        self.token: str = config.tokens['telegram']
        self.config: BotConfig = config
        self.object_provider: ObjectProvider = object_provider
        self.database: Database = database
        self.plugin_collection: PluginCollection = None

    def initialize(self):
        self.scheduler = Scheduler(self)
        tasks: List[Task] = self.object_provider.query_objects(self.database, 'data.Task', None, None)
        self.scheduler.initialize(tasks)
        ip: str = utils.get_ip_address()
        chats: List[Chat] = self.object_provider.query_objects(self.database, 'data.Chat', None, None)
        chat: Chat
        for chat in chats:
            try:
                self.send_message(chat, 'Pancho initialized in host {ip}'.format(ip=ip), MessageStyle.NONE)
            except Exception as ex:
                logging.error('Could not send message to chat {c}.'.format(c=chat.id_chat), ex)
        self.plugin_collection = PluginCollection('plugins')
        plugin: Plugin
        for plugin in self.plugin_collection:
            try:
                plugin.on_load(self)
            except Exception as e:
                logging.error('Could not load plugin {p}'.format(p=plugin.name()), e)
                self.broadcast('Could not load plugin {p}'.format(p=plugin.name()), MessageStyle.NONE)

    def run(self):
        while self.running:
            logging.info('Waiting for messages...')
            try:
                response: GetUpdatesResponse = self.get_updates()
                for update in response.result:
                    if update.message is not None:
                        self.on_new_message(update.message)
                    if update.callback_query is not None:
                        self.on_new_callback_query(update.callback_query)
            except Exception as e:
                logging.exception(e)
                time.sleep(60)
        logging.info('Stopped')

    def base_url(self) -> str:
        return 'https://api.telegram.org/bot{t}/'.format(t=self.token)

    def call(self, action: str, params: Dict = None, timeout: float = socket._GLOBAL_DEFAULT_TIMEOUT) -> Dict:
        if params is not None:
            req = urllib.request.Request(self.base_url() + action, urllib.parse.urlencode(utils.dict_to_url_params(params)).encode('ascii'))
        else:
            req = urllib.request.Request(self.base_url() + action)
        try:
            response: http.client.HTTPResponse
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status == 200:
                    received_bytes: bytes = response.read()
                    received_str: str = received_bytes.decode("utf8")
                else:
                    raise RuntimeError(f'Could not execute action {action}. Reason: {response.reason}')
        except urllib.error.URLError as e:
            received_bytes: bytes = e.read()
            received_obj = json.loads(received_bytes.decode("utf8"))
            raise RuntimeError(
                f'Could not execute action {action}. Error: {received_obj["error_code"]}. Reason: {received_obj["description"]}')

        # noinspection PyUnboundLocalVariable
        logging.info(f'Received response: {received_str}')
        return json.loads(received_str)

    def get_updates(self) -> GetUpdatesResponse:

        last_update_id: Optional[int] = self.get_last_update_id()
        if last_update_id is None:
            json_resp: Dict = self.call('getUpdates',
                                        {"timeout": self.config.get_updates_timeout},
                                        timeout=self.config.get_updates_timeout)
        else:
            json_resp: Dict = self.call('getUpdates',
                                        {"timeout": self.config.get_updates_timeout, "offset": last_update_id + 1},
                                        timeout=self.config.get_updates_timeout)
        res: GetUpdatesResponse = GetUpdatesResponse.from_json(json_resp)

        if len(res.result) == 0:
            return res

        ds: DataSet = DataSet()
        for result in res.result:
            ds.merge(result.to_data_set)

        last_update_id: int = max(r.id_update for r in res.result)
        last_update_id_row: DataRow = DataRow('parameter', 'last_update_id')
        last_update_id_row.put('key', 'last_update_id')
        last_update_id_row.put('value', str(last_update_id))
        ds.merge_row(last_update_id_row)

        connection: Connection = self.database.create_connection()
        self.database.save_data_set(connection, ds)
        connection.commit()

        return res

    def send_admin(self, text: Union[str, TextFormatter], style: MessageStyle) -> List[Message]:
        # res = []
        # chats = self.object_provider.query_objects(self.database, 'data.Chat', 'id_', None)  # type: List[Chat]
        # for chat in chats:
        #     res.append(self.send_message(chat, text, style))
        # return res
        raise NotImplementedError()

    def send_message(self, chat: Chat, text: Union[str, TextFormatter], style: MessageStyle) -> Message:
        if type(text) is TextFormatter:
            message_params: Dict = {'chat_id': chat.id_chat, 'text': text.format(style)}
        else:
            message_params: Dict = {'chat_id': chat.id_chat, 'text': text}
        if style == MessageStyle.MARKDOWN:
            message_params['parse_mode'] = 'Markdown'
        elif style == MessageStyle.HTML:
            message_params['parse_mode'] = 'HTML'
        resp: Dict = self.call('sendMessage', message_params)
        sent_message: Message = Message.from_json(resp['result'])
        self.database.save(sent_message)
        return sent_message

    def broadcast(self, text: Union[str, TextFormatter], style: MessageStyle):
        chats: List[Chat] = self.object_provider.query_objects(self.database, 'data.Chat', None, None)
        for chat in chats:
            self.send_message(chat, text, style)

    def send_message_with_inline_keyboard(self, chat: Chat, text: str, style: MessageStyle, inline_keyboard: InlineKeyboardMarkup) -> Message:
        message_params: Dict = {'chat_id': chat.id_chat, 'text': text, 'reply_markup': inline_keyboard.to_json()}
        if style == MessageStyle.MARKDOWN:
            message_params['parse_mode'] = 'Markdown'
        elif style == MessageStyle.HTML:
            message_params['parse_mode'] = 'HTML'
        resp = self.call('sendMessage', message_params)
        sent_message: Message = Message.from_json(resp['result'])
        self.database.save(sent_message)
        return sent_message

    def send_document(self, chat: Chat, filename: str) -> None:
        subprocess.call(['curl', '-F', 'chat_id=' + str(chat.id_chat), '-F', 'document=@"{x}"'.format(x=filename),
                         self.base_url() + 'sendDocument'])

    def answer_callback_query(self, callback_query_id: str) -> None:
        self.call('answerCallbackQuery', {'callback_query_id': callback_query_id})

    def get_last_update_id(self) -> Optional[int]:
        connection = self.database.create_connection()
        ds: DataSet = self.database.query(connection, 'parameter', 'last_update_id', False)
        dt = ds.tables['parameter']
        if len(dt.rows) > 0:
            return int(list(dt.rows.values())[0].get('value'))
        else:
            return None

    def on_new_message(self, message: Message) -> None:
        chat_state: ChatState = message.chat.retrieve_chat_state()

        instance: MessageHandlerBase = self.message_handlers['base']()
        instance.handler_name = 'base'
        try:
            instance.process_message(message, self, chat_state)
        except Exception as ex:
            self.send_message(message.chat, f'Error: {str(ex)}', MessageStyle.NONE)
            logging.exception(ex)

        if chat_state is not None:
            instance = self.message_handlers[chat_state.current_handler_name]()
            instance.handler_name = chat_state.current_handler_name
            try:
                instance.process_message(message, self, chat_state)
            except Exception as ex:
                self.send_message(message.chat, f'Error: {str(ex)}', MessageStyle.NONE)
        else:
            handler_name: str
            for handler_name in self.message_handlers:
                if handler_name != 'base':
                    instance = self.message_handlers[handler_name]()
                    instance.handler_name = handler_name
                    try:
                        instance.process_message(message, self)
                    except Exception as ex:
                        self.send_message(message.chat, f'Error: {str(ex)}', MessageStyle.NONE)
                        logging.exception(ex)

    def on_new_callback_query(self, callback_query: CallbackQuery) -> None:
        chat_state: ChatState = callback_query.message.chat.retrieve_chat_state()
        if chat_state is not None:
            instance: MessageHandlerBase = self.message_handlers[chat_state.current_handler_name]()
            instance.handler_name = chat_state.current_handler_name
            try:
                instance.process_callback_query(callback_query, self, chat_state)
            except Exception as ex:
                self.send_message(callback_query.message.chat, f'Error: {str(ex)}', MessageStyle.NONE)
        else:
            self.send_message(callback_query.message.chat, 'Could not retrieve chat state', MessageStyle.NONE)

    def execute_task(self, task: Task) -> None:
        self.send_message(task.chat, 'This is a task!', MessageStyle.MARKDOWN)




