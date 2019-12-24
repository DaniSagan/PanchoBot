import urllib.request
import urllib.parse
import http.client
import json
from typing import List, Optional, Dict

from db.database import Database, DataRow, DbSerializable, DataSet


class GetUpdatesResponse(object):
    def __init__(self):
        self.ok = False  # type: bool
        self.result = []  # type: List[Update]

    @staticmethod
    def from_json(json_obj) -> 'GetUpdatesResponse':
        res = GetUpdatesResponse()
        res.ok = json_obj['ok']
        res.result = [Update.from_json(x) for x in json_obj['result']]
        return res


class BotConfig(object):
    def __init__(self):
        self.database_definition_file = None  # type: Optional[str]
        self.get_updates_timeout = 0  # type: int

    @staticmethod
    def from_json(json_object: Dict) -> 'BotConfig':
        res = BotConfig()  # type: BotConfig
        res.database_definition_file = json_object.get('database_definition_file')
        res.get_updates_timeout = json_object.get('get_updates_timeout')
        return res


class Update(DbSerializable):
    def __init__(self):
        self.id_update = 0  # type: int
        self.message = None  # type: Message

    @staticmethod
    def from_json(json_obj) -> 'Update':
        res = Update()  # type: Update
        res.id_update = json_obj['update_id']
        res.message = Message.from_json(json_obj['message'])
        return res

    def to_data_set(self) -> DataSet:
        res = DataSet()
        row = DataRow('update', self.id_update)
        row.put('id_update', self.id_update)
        row.put('id_message', self.message.id_message)
        res.merge_row(row)
        res.merge(self.message.to_data_set())
        return res


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


# class Bot(object):
#
#     def __init__(self, token: str, config: BotConfig):
#         self.token = token  # type: str
#         self.config = config  # type: BotConfig
#         self.database = None  # type: Optional[Database]
#
#     def initialize(self):
#         with open(self.config.database_definition_file) as fobj:
#             db_definition_str = fobj.read()  # type: str
#         self.database = Database.from_json(json.loads(db_definition_str))
#         self.database.create_tables()
#
#     def run(self):
#         running = True
#         while running:
#             response = self.get_updates()  # type: GetUpdatesResponse
#             for update in response.result:
#                 self.on_new_message(update.message)
#
#     def base_url(self) -> str:
#         return 'https://api.telegram.org/bot{t}/'.format(t=self.token)
#
#     def call(self, action: str, params: Dict = None) -> Dict:
#         if params is not None:
#             req = urllib.request.Request(self.base_url() + action, urllib.parse.urlencode(params).encode('ascii'))
#         else:
#             req = urllib.request.Request(self.base_url() + action)
#         with urllib.request.urlopen(req) as response:  # type:  http.client.HTTPResponse
#             if response.status == 200:
#                 received_bytes = response.read()  # type: bytes
#                 received_str = received_bytes.decode("utf8")  # type: str
#             else:
#                 raise RuntimeError('Could not execute action {a}. Reason: {r}'.format(a=action, r=response.reason))
#
#         # noinspection PyUnboundLocalVariable
#         print('Received response: {r}'.format(r=received_str))
#         return json.loads(received_str)
#
#     def get_updates(self) -> GetUpdatesResponse:
#
#         last_update_id = self.get_last_update_id()  # type: Optional[int]
#
#         json_resp = self.call('getUpdates', {"timeout": self.config.get_updates_timeout, "offset": last_update_id+1})
#         res = GetUpdatesResponse.from_json(json_resp)
#
#         ds = DataSet()  # type: DataSet
#         for result in res.result:
#             ds.merge(result.to_data_set())
#
#         last_update_id = max(r.id_update for r in res.result)  # type: int
#         last_update_id_row = DataRow('parameter', 'last_update_id')
#         last_update_id_row.put('key', 'last_update_id')
#         last_update_id_row.put('value', str(last_update_id))
#         ds.merge_row(last_update_id_row)
#
#         connection = self.database.create_connection()
#         self.database.save_data_set(connection, ds)
#         connection.commit()
#
#         return res
#
#     def send_message(self, chat: Chat, text: str) -> Message:
#         message_params = {'chat_id': chat.id_chat, 'text': text}
#         resp = self.call('sendMessage', message_params)
#         sent_message = Message.from_json(resp['result'])
#         self.database.save(sent_message)
#         return sent_message
#
#     def get_last_update_id(self) -> Optional[int]:
#         connection = self.database.create_connection()
#         dt = self.database.query(connection, 'parameter', 'last_update_id', False)  # type: DataTable
#         if len(dt.rows) > 0:
#             return int(list(dt.rows.values())[0].get('value'))
#         else:
#             return None
#
#     def on_new_message(self, message: Message):
#         pass