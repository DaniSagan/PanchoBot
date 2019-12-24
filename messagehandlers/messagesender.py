from bot import MessageHandlerBase, BotBase
from data import Message, Chat, ChatState
from db.database import DataTable, DataSet


class MessageSender(MessageHandlerBase):
    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None):
        words = message.text.split(' ')
        if words[0].lower() == 'msg':
            if words[1].lower() == 'who':
                with bot.database.create_connection() as connection:
                    dt = bot.database.query(connection, 'chat', None, False)  # type: DataTable
                res = ''
                for row in dt.rows.values():
                    res += '{i}: {fn} - {ln}\n'.format(i=row.get('id_chat'), fn=row.get('first_name'), ln=row.get('last_name'))
                bot.send_message(message.chat, res)
            if words[1].lower() == 'send':
                other_chat_id = int(words[2])
                with bot.database.create_connection() as connection:
                    dt = bot.database.query(connection, 'chat', other_chat_id, False)  # type: DataTable
                if len(dt.rows) > 0:
                    ds = DataSet()  # type: DataSet
                    ds.tables['chat'] = dt
                    other_chat = Chat.from_data_set(ds)
                    bot.send_message(other_chat, ' '.join(words[3:]))
