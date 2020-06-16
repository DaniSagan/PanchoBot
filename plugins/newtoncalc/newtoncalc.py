import time
from typing import Dict, List
from typing import List

import utils
from bot.base import MessageHandlerBase, BotBase
from data import Message, ChatState
from textformatting import TextFormatter, MessageStyle

OPERATION_EXAMPLES: Dict[str, str] = {
    'simplify': 'simplify 2^2+2(2)',
    'factor': 'factor x^2 + 2x',
    'derive': 'derive x^2+2x',
    'integrate': 'integrate x^2+2x',
    'zeroes': 'zeroes x^2+2x',
    'tangent': 'tangent 2|x^3',
    'area': 'area 2:4|x^3',
    'cos': 'cos/pi',
    'sin': 'sin/0'
}


class NewtonCalcResponse(object):
    def __init__(self):
        self.operation: str = ''
        self.expression: str = ''
        self.result: str = ''
        self.error: str = ''

    @staticmethod
    def from_json(json_obj: Dict) -> 'NewtonCalcResponse':
        res: NewtonCalcResponse = NewtonCalcResponse()
        res.operation = json_obj.get('operation')
        res.expression = json_obj.get('expression')
        res.result = json_obj.get('result')
        res.error = json_obj.get('error')
        return res


class NewtonCalcMessageHandler(MessageHandlerBase):
    @staticmethod
    def get_help() -> TextFormatter:
        res: TextFormatter = TextFormatter()
        res.italic('\U00002328 Newton').new_line()
        res.normal('Start a new session.').new_line().new_line()
        res.italic('\U00002328 <operation> <expression>').new_line()
        res.normal('Apply <operation> on <expression>.').new_line().new_line()
        res.normal('Examples:').new_line()
        operation: str
        for operation in OPERATION_EXAMPLES:
            res.italic('  ' + OPERATION_EXAMPLES[operation]).new_line()
        res.new_line()
        res.normal('Type "Quit" to exit')
        return res

    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None):
        if chat_state is not None:
            self.process_state(message, bot, chat_state)
        else:
            self.process_new_message(message, bot)

    def process_state(self, message: Message, bot: BotBase, chat_state: ChatState):
        words: List[str] = message.text.split(' ')
        operation: str = words[0].lower()
        expression: str = ''.join(words[1:])
        json_obj = utils.get_url_json(f'https://newton.now.sh/{operation}/{expression}')
        res: NewtonCalcResponse = NewtonCalcResponse.from_json(json_obj)
        if res.error:
            bot.send_message(message.chat, 'Error: ' + res.error, MessageStyle.NONE)
        else:
            result_msg: str = res.result
            bot.send_message(message.chat, result_msg, MessageStyle.NONE)

    def process_new_message(self, message: Message, bot: BotBase):
        words: List[str] = message.text.split(' ')
        if words[0].lower() == 'newton':

            bot.send_message(message.chat,
                             'Newton Calc. Give me an operation and an expression. Type \'quit\' to exit:',
                             MessageStyle.NONE)

            state: ChatState = ChatState()
            state.last_time = time.time()
            state.chat_id = message.chat.id_chat
            state.current_handler_name = self.handler_name
            message.chat.save_chat_state(state)
