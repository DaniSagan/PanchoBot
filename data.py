import urllib.request
import http.client
import json
from typing import List, Optional, Dict

from db.database import Database, Table, Row


class GetUpdatesResponse(object):
    def __init__(self):
        self.ok = False  # type: bool
        self.result = None  # type: Optional[List[Update]]

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
    def from_json(json: Dict) -> 'BotConfig':
        res = BotConfig()  # type: BotConfig
        res.database_definition_file = json.get('database_definition_file')
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
        mybytes = response.read()  # type: bytes
        mystr = mybytes.decode("utf8")  # type: str
        response.close()

        print('Received response: {r}'.format(r=mystr))
        j = json.loads(mystr)
        res = GetUpdatesResponse.from_json(j)
        return res


class Update(object):
    def __init__(self):
        self.update_id = 0  # type: int
        self.message = None  # type: Optional[Message]

    @staticmethod
    def from_json(json_obj) -> 'Update':
        res = Update()  # type: Update
        res.update_id = json_obj['update_id']
        res.message = Message.from_json(json_obj['message'])
        return res


class Message(object):
    def __init__(self):
        self.message_id = 0  # type: int
        self._from = None  # type: Optional[User]
        self.date = None  # type: Optional[int]
        self.text = None  # type: Optional[str]

    @staticmethod
    def from_json(json_obj) -> 'Message':
        res = Message()  # type: Message
        res.message_id = json_obj['message_id']
        res._from = User.from_json(json_obj['from'])
        res.date = json_obj['date']
        res.text = json_obj['text']
        return res


class User(object):
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

    def to_row(self, database: Database) -> Row:
        res = Row()
        res.table_name = 'user'
        res.put('id_user', self.id_user)
        res.put('is_bot', self.is_bot)
        res.put('first_name', self.first_name)
        res.put('last_name', self.last_name)
        res.put('username', self.username)
        res.put('language_code', self.language_code)
        return res

