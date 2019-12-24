import http.client
from data import GetUpdatesResponse, Chat, Message, BotConfig
from db.database import Database, DataSet, DataRow, DataTable
import json
from typing import Dict, Optional, List
import urllib.request
import urllib.parse


class BotBase(object):
    def __init__(self):
        self.database = None  # type: Database
        self.running = True

    def get_updates(self) -> GetUpdatesResponse:
        raise NotImplementedError()

    def send_message(self, chat: Chat, text: str) -> Message:
        raise NotImplementedError()

    def stop(self):
        self.running = False


class MessageHandlerBase(object):
    def __init__(self):
        pass

    def process_message(self, message: Message, bot: BotBase):
        raise NotImplementedError()


class Bot(BotBase):

    def __init__(self, token: str, config: BotConfig):
        BotBase.__init__(self)
        self.token = token  # type: str
        self.config = config  # type: BotConfig
        self.message_handlers = []  # type: List[MessageHandlerBase]

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
                self.on_new_message(update.message)
        print('Stopped')

    def base_url(self) -> str:
        return 'https://api.telegram.org/bot{t}/'.format(t=self.token)

    def call(self, action: str, params: Dict = None) -> Dict:
        if params is not None:
            req = urllib.request.Request(self.base_url() + action, urllib.parse.urlencode(params).encode('ascii'))
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

    def send_message(self, chat: Chat, text: str) -> Message:
        message_params = {'chat_id': chat.id_chat, 'text': text}
        resp = self.call('sendMessage', message_params)
        sent_message = Message.from_json(resp['result'])
        self.database.save(sent_message)
        return sent_message

    def get_last_update_id(self) -> Optional[int]:
        connection = self.database.create_connection()
        dt = self.database.query(connection, 'parameter', 'last_update_id', False)  # type: DataTable
        if len(dt.rows) > 0:
            return int(list(dt.rows.values())[0].get('value'))
        else:
            return None

    def on_new_message(self, message: Message):
        for handler in self.message_handlers:
            try:
                handler.process_message(message, self)
            except Exception as ex:
                self.send_message(message.chat, 'Error: {e}'.format(e=str(ex)))
