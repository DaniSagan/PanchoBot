import time
from typing import Dict

import utils
from bot import MessageHandlerBase, BotBase
from data import Message, ChatState


class NewtonCalcResponse(object):
    def __init__(self):
        self.operation = ''  # type: str
        self.expression = ''  # type: str
        self.result = ''  # type: str
        self.error = ''  # type: str

    @staticmethod
    def from_json(json_obj: Dict) -> 'NewtonCalcResponse':
        res = NewtonCalcResponse()
        res.operation = json_obj.get('operation')
        res.expression = json_obj.get('expression')
        res.result = json_obj.get('result')
        res.error = json_obj.get('error')
        return res


class NewtonCalc(MessageHandlerBase):
    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None):
        if chat_state is not None:
            self.process_state(message, bot, chat_state)
        else:
            self.process_new_message(message, bot)

    def process_state(self, message: Message, bot: BotBase, chat_state: ChatState):
        words = message.text.split(' ')  # type: List[str]
        operation = words[0].lower()  # type: str
        expression = ''.join(words[1:])  # type: str
        json_obj = utils.get_url_json('https://newton.now.sh/{o}/{e}'.format(o=operation, e=expression))
        res = NewtonCalcResponse.from_json(json_obj)  # type: NewtonCalcResponse
        if res.error:
            bot.send_message(message.chat, 'Error: ' + res.error)
        else:
            result_msg = res.result  # type: str
            bot.send_message(message.chat, result_msg)

    def process_new_message(self, message: Message, bot: BotBase):
        words = message.text.split(' ')
        if words[0].lower() == 'newton':

            bot.send_message(message.chat, 'Newton Calc. Give me an operation and an expression. Type \'quit\' to exit:')

            state = ChatState()
            state.last_time = time.time()
            state.chat_id = message.chat.id_chat
            state.current_handler_name = self.handler_name
            message.chat.save_chat_state(state)
