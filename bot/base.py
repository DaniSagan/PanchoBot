from typing import Union, List, Dict

from data import CallbackQuery, Message, ChatState, GetUpdatesResponse, Chat
from db.database import Database
from scheduler import Scheduler
from textformatting import TextFormatter, MessageStyle


class InlineKeyboardButton(object):
    def __init__(self):
        self.text: str = ''
        self.url: str = ''
        self.callback_data: str = ''

    def to_json(self) -> Dict:
        if self.url and not self.callback_data:
            return {'text': self.text, 'url': self.url}
        elif not self.url and self.callback_data:
            return {'text': self.text, 'callback_data': self.callback_data}


class InlineKeyboardMarkup(object):
    def __init__(self):
        self.inline_keyboard: List[List[InlineKeyboardButton]] = []

    @staticmethod
    def from_str_list(str_list: List[str]) -> 'InlineKeyboardMarkup':
        res: InlineKeyboardMarkup = InlineKeyboardMarkup()
        res.inline_keyboard.append([])
        s: str
        for s in str_list:
            button: InlineKeyboardButton = InlineKeyboardButton()
            button.text = s
            button.callback_data = s
            res.inline_keyboard[0].append(button)
        return res

    def to_json(self) -> Dict:
        return {'inline_keyboard': [[button.to_json() for button in row] for row in self.inline_keyboard]}


class BotBase(object):

    def __init__(self):
        self.database: Database = None
        self.running: bool = True
        self.tokens: Dict[str, str] = {}
        self.scheduler: Scheduler = None
        self.message_handlers: Dict[str, type] = {}

    def get_updates(self) -> GetUpdatesResponse:
        raise NotImplementedError()

    def send_admin(self, text: Union[str, TextFormatter], style: MessageStyle) -> Message:
        raise NotImplementedError()

    def send_message(self, chat: Chat, text: Union[str, TextFormatter], style: MessageStyle) -> Message:
        raise NotImplementedError()

    def broadcast(self, text: Union[str, TextFormatter], style: MessageStyle) -> Message:
        raise NotImplementedError()

    def send_document(self, chat: Chat, filename: str):
        raise NotImplementedError()

    def send_message_with_inline_keyboard(self, chat: Chat, text: str, style: MessageStyle, inline_keyboard: InlineKeyboardMarkup) -> Message:
        raise NotImplementedError()

    def answer_callback_query(self, callback_query_id: str) -> bool:
        raise NotImplementedError()

    def stop(self):
        self.running = False

    def add_message_handler(self, handler_name: str, handler_type: type) -> None:
        if handler_name in self.message_handlers:
            raise ValueError(handler_name + ' already added.')
        self.message_handlers[handler_name] = handler_type


class MessageHandlerBase(object):
    def __init__(self):
        self.handler_name: str = ''

    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None) -> None:
        raise NotImplementedError()

    def process_callback_query(self, callback_query: CallbackQuery, bot: BotBase, chat_state: ChatState = None) -> None:
        bot.send_message(callback_query.message.chat,
                         f'process_callback_query not defined for handler {self.handler_name}',
                         MessageStyle.NONE)

    @staticmethod
    def get_help() -> TextFormatter:
        return TextFormatter.instance().normal('Help message not defined.')

    @staticmethod
    def get_info() -> TextFormatter:
        return TextFormatter.instance().normal('Undefined handler')

