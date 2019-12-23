import urllib.request
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

    @staticmethod
    def from_json(json_object: Dict) -> 'BotConfig':
        res = BotConfig()  # type: BotConfig
        res.database_definition_file = json_object.get('database_definition_file')
        return res


class Bot(object):

    def __init__(self, token: str, config: BotConfig):
        self.token = token  # type: str
        self.config = config  # type: BotConfig
        self.database = None  # type: Optional[Database]

    def initialize(self):
        with open(self.config.database_definition_file) as fobj:
            db_definition_str = fobj.read()  # type: str
        self.database = Database.from_json(json.loads(db_definition_str))
        self.database.create_tables()

    def base_url(self) -> str:
        return 'https://api.telegram.org/bot{t}/'.format(t=self.token)

    def get_updates(self) -> GetUpdatesResponse:
        response = urllib.request.urlopen(self.base_url() + 'getUpdates')  # type:  http.client.HTTPResponse
        received_bytes = response.read()  # type: bytes
        received_str = received_bytes.decode("utf8")  # type: str
        response.close()

        print('Received response: {r}'.format(r=received_str))
        j = json.loads(received_str)
        res = GetUpdatesResponse.from_json(j)

        dtc = DataSet()
        for result in res.result:
            dtc.merge(result.to_data_set())

        last_update_id = max(r.id_update for r in res.result)
        last_update_id_row = DataRow('parameter', 'last_update_id')
        last_update_id_row.put('key', 'last_update_id')
        last_update_id_row.put('value', str(last_update_id))
        dtc.merge_row(last_update_id_row)

        connection = self.database.create_connection()
        self.database.save_data_set(connection, dtc)
        connection.commit()

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


class Message(DbSerializable):
    def __init__(self):
        self.id_message = 0  # type: int
        self._from = None  # type: Optional[User]
        self.date = None  # type: Optional[int]
        self.text = None  # type: Optional[str]

    @staticmethod
    def from_json(json_obj) -> 'Message':
        res = Message()  # type: Message
        res.id_message = json_obj['message_id']
        res._from = User.from_json(json_obj['from'])
        res.date = json_obj['date']
        res.text = json_obj['text']
        return res

    def to_data_set(self) -> DataSet:
        res = DataSet()
        row = DataRow('message', self.id_message)
        row.put('id_message', self.id_message)
        row.put('id_user', self._from.id_user)
        row.put('date', self.date)
        row.put('text', self.text)
        res.merge_row(row)
        res.merge(self._from.to_data_set())
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
        res.last_name = json_obj['last_name']
        res.username = json_obj.get('username')
        res.language_code = json_obj['language_code']
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


