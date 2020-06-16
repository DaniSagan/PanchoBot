import uuid
from pathlib import Path
from typing import List, Optional, Dict
import pickle
import pathlib
import time

import sqlite3

import jsonutils
import utils
from db.database import DataRow, DbSerializable, DataSet, Database
from jsonutils import JsonDeserializable


class GetUpdatesResponse(JsonDeserializable):
    def __init__(self):
        self.ok: bool = False
        self.result: List[Update] = []

    @classmethod
    def from_json(cls, json_obj: Dict) -> 'GetUpdatesResponse':
        res: GetUpdatesResponse = GetUpdatesResponse()
        res.ok = json_obj['ok']
        res.result = [Update.from_json(x) for x in json_obj['result']]
        return res


class BotConfig(JsonDeserializable):
    def __init__(self):
        self.database_definition_file: Optional[str] = None
        self.object_provider_file: str = None
        self.get_updates_timeout: int = 0
        self.tokens: Dict[str, str] = {}
        # self.specific_config = {}  # type: Dict
        self.administrator_id: int = 0

    @classmethod
    def from_json(cls, json_object: Dict) -> 'BotConfig':
        res: BotConfig = BotConfig()
        res.database_definition_file = json_object.get('database_definition_file')
        res.object_provider_file = json_object.get('object_provider_file')
        res.get_updates_timeout = json_object.get('get_updates_timeout')
        res.tokens = utils.get_file_json(json_object['token_file'])
        specific_config = utils.get_file_json(json_object['specific_config_file'])
        res.administrator_id = specific_config['administrator_id']
        return res


class Update(DbSerializable, JsonDeserializable):
    def __init__(self):
        self.id_update: int = 0
        self.message: Message or None = None
        self.callback_query: CallbackQuery or None = None

    @classmethod
    def from_json(cls, json_obj: Dict) -> 'Update':
        res: Update = Update()
        res.id_update = json_obj['update_id']
        res.message = Message.from_json(json_obj['message']) if 'message' in json_obj else None
        res.callback_query = CallbackQuery.from_json(json_obj['callback_query']) if 'callback_query' in json_obj else None
        return res

    @property
    def to_data_set(self) -> DataSet:
        res: DataSet = DataSet()
        row = DataRow('update', self.id_update)
        row.put('id_update', self.id_update)
        row.put('id_message', self.message.id_message if self.message is not None else None)
        res.merge_row(row)
        if self.message is not None:
            res.merge(self.message.to_data_set())
        return res


class ChatState(object):
    def __init__(self):
        self.current_handler_name: str = None
        self.last_time: float = 0.
        self.chat_id: int = 0
        self.data: Dict = {}


class Chat(DbSerializable, JsonDeserializable):
    def __init__(self):
        self.id_chat: int = 0
        self.first_name: str = None
        self.last_name: str = None
        self.type: str = None

    @classmethod
    def from_json(cls, json_obj: Dict) -> 'Chat':
        res: Chat = Chat()
        res.id_chat = json_obj['id']
        res.type = json_obj['type']
        res.first_name = json_obj.get('first_name')
        res.last_name = json_obj.get('last_name')
        return res

    def to_data_set(self) -> DataSet:
        res: DataSet = DataSet()
        row = DataRow('chat', self.id_chat)
        row.put('id_chat', self.id_chat)
        row.put('type', self.type)
        row.put('first_name', self.first_name)
        row.put('last_name', self.last_name)
        res.merge_row(row)
        return res

    @classmethod
    def from_data_set(cls, ds: DataSet) -> 'Chat':
        res: Chat = Chat()
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

    def retrieve_chat_state(self) -> ChatState or None:
        folder: pathlib.Path = pathlib.Path('chat')
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
        folder: pathlib.Path = pathlib.Path('chat')
        if not folder.exists():
            folder.mkdir()
        filename = folder.joinpath(f'{self.id_chat}.pickle')
        with open(str(filename), 'wb') as fobj:
            pickle.dump(chat_state, fobj)

    def remove_chat_state(self) -> None:
        folder: pathlib.Path = pathlib.Path('chat')
        if not folder.exists():
            return
        filename: Path = folder.joinpath(f'{self.id_chat}.pickle')
        if filename.exists():
            filename.unlink()


class Message(DbSerializable, JsonDeserializable):
    def __init__(self):
        self.id_message: int = 0
        self._from: Optional[User] = None
        self.date: Optional[int] = None
        self.text: Optional[str] = None
        self.chat: Optional[Chat] = None
        self.photo: List[PhotoSize] = []

    @classmethod
    def from_json(cls, json_obj: Dict) -> 'Message':
        res: Message = Message()
        res.id_message = json_obj['message_id']
        res._from = User.from_json(json_obj['from'])
        res.chat = Chat.from_json(json_obj['chat'])
        res.date = json_obj['date']
        res.text = json_obj.get('text')
        res.photo = [PhotoSize.from_json(x) for x in json_obj.get('photo')] if 'photo' in json_obj else None
        return res

    def to_data_set(self) -> DataSet:
        res: DataSet = DataSet()
        row: DataRow = DataRow('message', self.id_message)
        row.put('id_message', self.id_message)
        row.put('id_user', self._from.id_user)
        row.put('id_chat', self.chat.id_chat)
        row.put('date', self.date)
        row.put('text', self.text)
        res.merge_row(row)
        res.merge(self._from.to_data_set())
        res.merge(self.chat.to_data_set())
        if self.photo is not None:
            photo_size: PhotoSize
            for photo_size in self.photo:
                res.merge(photo_size.to_data_set())
                res.add_column_to_table('photo_size', 'id_message', self.id_message)
        return res


class CallbackQuery(DbSerializable, JsonDeserializable):
    def __init__(self):
        self.id_callback_query: str = ''
        self._from: User = None
        self.message: Message = None
        self.inline_message_id: str = None
        self.chat_instance: str = None
        self.data: str = None

    @classmethod
    def from_json(cls, json_obj: Dict) -> 'CallbackQuery':
        res: CallbackQuery = CallbackQuery()
        res.id_callback_query = json_obj['id']
        res._from = User.from_json(json_obj['from'])
        res.message = Message.from_json(json_obj['message']) if 'message' in json_obj else None
        res.inline_message_id = json_obj.get('inline_message_id')
        res.chat_instance = json_obj['chat_instance']
        res.data = json_obj.get('data')
        return res

    def to_data_set(self) -> DataSet:
        res: DataSet = DataSet()
        row: DataRow = DataRow('callback_query', self.id_callback_query)
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


class User(DbSerializable, JsonDeserializable):
    def __init__(self):
        self.id_user: int = 0
        self.is_bot: bool = False
        self.first_name: Optional[str] = None
        self.last_name: Optional[str] = None
        self.username: Optional[str] = None
        self.language_code: Optional[str] = None

    @classmethod
    def from_json(cls, json_obj: Dict) -> 'User':
        res: User = User()
        res.id_user = json_obj['id']
        res.is_bot = json_obj['is_bot']
        res.first_name = json_obj['first_name']
        res.last_name = json_obj.get('last_name')
        res.username = json_obj.get('username')
        res.language_code = json_obj.get('language_code')
        return res

    def to_data_set(self):
        res: DataSet = DataSet()
        row: DataRow = DataRow('user', self.id_user)
        row.put('id_user', self.id_user)
        row.put('is_bot', self.is_bot)
        row.put('first_name', self.first_name)
        row.put('last_name', self.last_name)
        row.put('username', self.username)
        row.put('language_code', self.language_code)
        res.merge_row(row)
        return res


class PhotoSize(DbSerializable, JsonDeserializable):
    def __init__(self):
        self.file_id: str = None
        self.file_unique_id: str = None
        self.width: int = 0
        self.height: int = 0
        self.file_size: int = 0

    @classmethod
    def from_json(cls, json_object: Dict) -> 'PhotoSize':
        res: PhotoSize = PhotoSize()
        res.file_id = json_object['file_id']
        res.file_unique_id = json_object['file_unique_id']
        res.width = json_object['width']
        res.height = json_object['height']
        res.file_size = json_object['file_size']
        return res

    def to_data_set(self) -> DataSet:
        res: DataSet = DataSet()
        row: DataRow = DataRow('photo_size', self.file_id)
        row.put('file_id', self.file_id)
        row.put('file_unique_id', self.file_unique_id)
        row.put('width', self.width)
        row.put('height', self.height)
        row.put('file_size', self.file_size)
        res.merge_row(row)
        return res


class Schedule(object):
    def __init__(self):
        self.id_schedule: uuid = uuid.uuid1()
        self.start: int = 0
        self.end: int = 0
        self.last_execution: int = 0
        self.interval_seconds: int = 0

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
        self.id_task: uuid = uuid.uuid1()
        self.chat: Chat = None
        self.schedule: Schedule = None

    def to_data_set(self) -> DataSet:
        res: DataSet = DataSet()
        row: DataRow = DataRow('task', self.id_task)
        row.put('id_task', str(self.id_task))
        res.merge_row(row)
        return res

    @classmethod
    def from_data_set(cls, data_set: DataSet) -> List['Task']:
        pass

    @classmethod
    def get_by_id(cls, database: Database, connection: sqlite3.Connection, id_object: object) -> 'Task':
        res: Task = Task()
        row: DataRow or None = database.query_row(connection, 'task', id_object)
        res.chat = Chat.get_by_id(database, connection, row.get('id_chat'))
        return res


class Profile(DbSerializable):
    def __init__(self):
        self.id_profile: uuid = uuid.uuid1()
        self.name: str = None

    def to_data_set(self) -> DataSet:
        res: DataSet = DataSet()
        row: DataRow = DataRow('id_profile', self.id_profile)
        row.put('id_profile', str(self.id_profile))
        row.put('name', self.name)
        res.merge_row(row)
        return res

    @classmethod
    def from_data_set(cls, data_set: DataSet) -> List['DbSerializable']:
        pass


class UserProfile(DbSerializable):
    def __init__(self):
        self.id_user_profile: uuid = uuid.uuid1()
        self.id_user: int = 0
        self.id_user_profile: uuid = None

    def to_data_set(self) -> DataSet:
        pass