import utils
from bot import MessageHandlerBase, BotBase
from data import Message, ChatState


class Trivia(MessageHandlerBase):
    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None):
        json_obj = utils.get_url_json('https://opentdb.com/api.php', {'amount': 1})
