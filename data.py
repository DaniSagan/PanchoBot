import uuid
from typing import List, Optional, Dict
import pickle
import pathlib
import time

import sqlite3

import utils
from db.database import DataRow, DbSerializable, DataSet, Database


class GetUpdatesResponse(object):
    def __init__(self):
        self.ok = False  # type: bool
        self.result = []  # type: List[Update]

    @staticmethod
    def from_json(json_obj: Dict) -> 'GetUpdatesResponse':
        res = GetUpdatesResponse()
        res.ok = json_obj['ok']
        res.result = [Update.from_json(x) for x in json_obj['result']]
        return res


class BotConfig(object):
    def __init__(self):
        self.database_definition_file = None  # type: Optional[str]
        self.object_provider_file = None  # type: str
        self.get_updates_timeout = 0  # type: int
        self.tokens = {}  # type: Dict[str, str]
        self.specific_config = {}  # type: Dict

    @staticmethod
    def from_json(json_object: Dict) -> 'BotConfig':
        res = BotConfig()  # type: BotConfig
        res.database_definition_file = json_object.get('database_definition_file')
        res.object_provider_file = json_object.get('object_provider_file')
        res.get_updates_timeout = json_object.get('get_updates_timeout')
        res.tokens = utils.get_file_json(json_object['token_file'])
        res.specific_config = utils.get_file_json(json_object['specific_config_file'])
        return res


class Update(DbSerializable):
    def __init__(self):
        self.id_update = 0  # type: int
        self.message = None  # type: Message
        self.callback_query = None  # type: CallbackQuery

    @staticmethod
    def from_json(json_obj) -> 'Update':
        res = Update()  # type: Update
        res.id_update = json_obj['update_id']
        res.message = Message.from_json(json_obj['message']) if 'message' in json_obj else None
        res.callback_query = CallbackQuery.from_json(json_obj['callback_query']) if 'callback_query' in json_obj else None
        return res

    def to_data_set(self) -> DataSet:
        res = DataSet()
        row = DataRow('update', self.id_update)
        row.put('id_update', self.id_update)
        row.put('id_message', self.message.id_message if self.message is not None else None)
        res.merge_row(row)
        if self.message is not None:
            res.merge(self.message.to_data_set())
        return res


class ChatState(object):
    def __init__(self):
        self.current_handler_name = None  # type: str
        self.last_time = 0.  # type: float
        self.chat_id = 0  # type: int
        self.data = {}  # type: Dict


class Chat(DbSerializable):
    def __init__(self):
        self.id_chat = 0  # type: int
        self.first_name = None  # type: str
        self.last_name = None  # type: str
        self.type = None  # type: str

    @staticmethod
    def from_json(json_obj) -> 'Chat':
        res = Chat()  # type: Chat
        res.id_chat = json_obj['id']
        res.type = json_obj['type']
        res.first_name = json_obj.get('first_name')
        res.last_name = json_obj.get('last_name')
        return res

    def to_data_set(self):
        res = DataSet()
        row = DataRow('chat', self.id_chat)
        row.put('id_chat', self.id_chat)
        row.put('type', self.type)
        row.put('first_name', self.first_name)
        row.put('last_name', self.last_name)
        res.merge_row(row)
        return res

    @staticmethod
    def from_data_set(ds: DataSet) -> 'Chat':
        res = Chat()  # type: Chat
        table = ds.tables['chat']
        row = list(table.rows.values())[0]
        res.id_chat = row.get('id_chat')
        res.type = row.get('type')
        res.first_name = row.get('first_name')
        res.last_name = row.get('last_name')
        return res

    @classmethod
    def get_by_id(cls, database: Database, connection: sqlite3.Connection, id_object: object) -> 'Chat':
        res = Chat()
        row = database.query_row(connection, 'chat', id_object)
        res.id_chat = row.get('id_chat')
        res.type = row.get('type')
        res.first_name = row.get('first_name')
        res.last_name = row.get('last_name')
        return res

    def retrieve_chat_state(self) -> ChatState:
        folder = pathlib.Path('chat')  # type: pathlib.Path
        if not folder.exists():
            return None
        filename = folder.joinpath('{id}.pickle'.format(id=self.id_chat))
        if filename.exists():
            with open(str(filename), 'rb') as fobj:
                data = pickle.load(fobj)
            return data
        else:
            return None

    def save_chat_state(self, chat_state: ChatState) -> None:
        folder = pathlib.Path('chat')  # type: pathlib.Path
        if not folder.exists():
            folder.mkdir()
        filename = folder.joinpath('{id}.pickle'.format(id=self.id_chat))
        with open(str(filename), 'wb') as fobj:
            pickle.dump(chat_state, fobj)

    def remove_chat_state(self):
        folder = pathlib.Path('chat')  # type: pathlib.Path
        if not folder.exists():
            return
        filename = folder.joinpath('{id}.pickle'.format(id=self.id_chat))
        if filename.exists():
            filename.unlink()


class Message(DbSerializable):
    def __init__(self):
        self.id_message = 0  # type: int
        self._from = None  # type: Optional[User]
        self.date = None  # type: Optional[int]
        self.text = None  # type: Optional[str]
        self.chat = None  # type: Optional[Chat]

    @staticmethod
    def from_json(json_obj) -> 'Message':
        res = Message()  # type: Message
        res.id_message = json_obj['message_id']
        res._from = User.from_json(json_obj['from'])
        res.chat = Chat.from_json(json_obj['chat'])
        res.date = json_obj['date']
        res.text = json_obj['text']
        return res

    def to_data_set(self) -> DataSet:
        res = DataSet()
        row = DataRow('message', self.id_message)
        row.put('id_message', self.id_message)
        row.put('id_user', self._from.id_user)
        row.put('id_chat', self.chat.id_chat)
        row.put('date', self.date)
        row.put('text', self.text)
        res.merge_row(row)
        res.merge(self._from.to_data_set())
        res.merge(self.chat.to_data_set())
        return res


class CallbackQuery(DbSerializable):
    def __init__(self):
        self.id_callback_query = ''  # type: str
        self._from = None  # type: User
        self.message = None  # type: Message
        self.inline_message_id = None  # type: str
        self.chat_instance = None  # type: str
        self.data = None  # type: str

    @staticmethod
    def from_json(json_obj) -> 'CallbackQuery':
        res = CallbackQuery()  # type: CallbackQuery
        res.id_callback_query = json_obj['id']
        res._from = User.from_json(json_obj['from'])
        res.message = Message.from_json(json_obj['message']) if 'message' in json_obj else None
        res.inline_message_id = json_obj.get('inline_message_id')
        res.chat_instance = json_obj['chat_instance']
        res.data = json_obj.get('data')
        return res

    def to_data_set(self) -> DataSet:
        res = DataSet()
        row = DataRow('callback_query', self.id_callback_query)
        row.put('id_callback_query', self.id_callback_query)
        row.put('id_user', self._from.id_user)
        row.put('id_message', self.message.id_message)
        row.put('inline_message_id', self.inline_message_id)
        row.put('chat_instance', self.chat_instance)
        row.put('data', self.data)
        res.merge_row(row)
        res.merge(self._from.to_data_set())
        res.merge(self.message.to_data_set())
        return res


class User(DbSerializable):
    def __init__(self):
        self.id_user = 0  # type: int
        self.is_bot = False  # type: bool
        self.first_name = None  # type: Optional[str]
        self.last_name = None  # type: Optional[str]
        self.username = None  # type: Optional[str]
        self.language_code = None  # type: Optional[str]

    @staticmethod
    def from_json(json_obj) -> 'User':
        res = User()  # type: User
        res.id_user = json_obj['id']
        res.is_bot = json_obj['is_bot']
        res.first_name = json_obj['first_name']
        res.last_name = json_obj.get('last_name')
        res.username = json_obj.get('username')
        res.language_code = json_obj.get('language_code')
        return res

    def to_data_set(self):
        res = DataSet()
        row = DataRow('user', self.id_user)
        row.put('id_user', self.id_user)
        row.put('is_bot', self.is_bot)
        row.put('first_name', self.first_name)
        row.put('last_name', self.last_name)
        row.put('username', self.username)
        row.put('language_code', self.language_code)
        res.merge_row(row)
        return res


class Schedule(object):
    def __init__(self):
        self.id_schedule = uuid.uuid1()  # type: uuid
        self.start = 0  # type: int
        self.end = 0  # type: int
        self.last_execution = 0  # type: int
        self.interval_seconds = 0  # type: int

    def next_execution(self) -> Optional[int]:
        if self.last_execution == 0:
            return self.start
        if self.interval_seconds == 0:
            return None
        expected_execution = self.last_execution + self.interval_seconds
        if self.start <= expected_execution <= self.end:
            return expected_execution
        else:
            return None


    # @classmethod
    # def from_data_set(cls, data_set: DataSet) -> List['DbSerializable']:
    #     pass
    #
    # def to_data_set(self) -> DataSet:
    #     res = DataSet()  # type: DataSet
    #     row = DataRow('schedule', str(self.id_schedule))  # type: DataRow
    #     row.put('id_schedule', str(self.id_schedule))
    #     res.merge_row(row)
    #     return res
    #
    # @classmethod
    # def get_by_id(cls, database: Database, connection: sqlite3.Connection, id_object: object) -> 'Schedule':
    #     res = Schedule()
    #     row = database.query_row(connection, 'schedule', id_object)
    #     res.id_schedule = id_object
    #     return res


class Task(DbSerializable):
    def __init__(self):
        self.id_task = uuid.uuid1()  # type: uuid
        self.chat = None  # type: Chat
        self.schedule = None  # type: Schedule

    def to_data_set(self) -> DataSet:
        res = DataSet()  # type: DataSet
        row = DataRow('task', self.id_task)  # type: DataRow
        row.put('id_task', str(self.id_task))
        res.merge_row(row)
        return res

    @classmethod
    def from_data_set(cls, data_set: DataSet) -> List['Task']:
        pass

    @classmethod
    def get_by_id(cls, database: Database, connection: sqlite3.Connection, id_object: object) -> 'Task':
        res = Task()
        row = database.query_row(connection, 'task', id_object)
        res.chat = Chat.get_by_id(database, connection, row.get('id_chat'))
        return res
