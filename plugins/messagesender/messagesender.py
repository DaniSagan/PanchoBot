from sqlite3.dbapi2 import Connection
from typing import List

from bot.base import MessageHandlerBase, BotBase
from data import Message, Chat, ChatState
from db.database import DataTable, DataSet, DataRow
from textformatting import MessageStyle


class MesageSenderMessageHandler(MessageHandlerBase):
    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None) -> None:
        words: List[str] = message.text.split(' ')
        if words[0].lower() == 'msg':
            if words[1].lower() == 'who':
                connection: Connection
                with bot.database.create_connection() as connection:
                    ds: DataSet = bot.database.query(connection, 'chat', None, False)
                    dt: DataTable = ds.tables['chat']
                res: str = ''
                row: DataRow
                for row in dt.rows.values():
                    res += f'{row.get("id_chat")}: {row.get("first_name")} - {row.get("last_name")}\n'
                bot.send_message(message.chat, res, MessageStyle.NONE)
            if words[1].lower() == 'send':
                other_chat_id = int(words[2])
                connection: Connection
                with bot.database.create_connection() as connection:
                    ds: DataSet = bot.database.query(connection, 'chat', other_chat_id, False)
                    dt: DataTable = ds.tables['chat']
                if len(dt.rows) > 0:
                    ds: DataSet = DataSet()
                    ds.tables['chat'] = dt
                    other_chat: Chat = Chat.from_data_set(ds)
                    bot.send_message(other_chat, ' '.join(words[3:]), MessageStyle.NONE)
