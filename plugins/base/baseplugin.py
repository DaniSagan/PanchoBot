from bot.base import BotBase, MessageHandlerBase
from bot.plugins import Plugin
from data import ChatState, Message
from textformatting import MessageStyle, TextFormatter


class BaseMessageHandler(MessageHandlerBase):
    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None) -> None:
        if message.text is not None:
            self.process_text(message, bot, chat_state)

    def process_text(self, message: Message, bot: BotBase, chat_state: ChatState) -> None:
        if message.text.lower() == 'status':
            if chat_state is not None:
                bot.send_message(message.chat,
                                 f'Current handler: {chat_state.current_handler_name}',
                                 MessageStyle.NONE)
            else:
                bot.send_message(message.chat, 'OK', MessageStyle.NONE)
        elif message.text.lower() == 'quit':
            message.chat.remove_chat_state()
        elif message.text.lower() == 'test':
            bot.send_document(message.chat, 'assets/test.png')
        elif message.text.lower() == 'help':
            if chat_state is None:
                tf = TextFormatter()  # TextFormatter
                for handler_name in bot.message_handlers:
                    tf.append(TextFormatter.instance().bold(handler_name).new_line()
                              .append(bot.message_handlers[handler_name].get_help()).new_line()
                              .normal('\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_').new_line())
                bot.send_message(message.chat, tf, MessageStyle.MARKDOWN)
            else:
                tf = TextFormatter()  # TextFormatter
                tf.append(TextFormatter.instance().bold(chat_state.current_handler_name).new_line()
                          .append(bot.message_handlers[chat_state.current_handler_name].get_help()).new_line()
                          .normal('\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_').new_line())
                bot.send_message(message.chat, tf, MessageStyle.MARKDOWN)


class BasePlugin(Plugin):
    def on_load(self, bot: BotBase) -> None:
        bot.add_message_handler('base', BaseMessageHandler)

    def name(self) -> str:
        return 'base'
