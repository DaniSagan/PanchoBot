import subprocess

from bot.base import MessageHandlerBase, BotBase
from data import Message, ChatState
from textformatting import MessageStyle


class PowerOff(MessageHandlerBase):
    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None):
        words = message.text.split(' ')
        if words[0].lower() == 'cmd':
            if words[1].lower() == 'poweroff':
                subprocess.call(['shutdown', '-h', '1'])
                bot.send_message(message.chat, 'Apagando....', MessageStyle.NONE)
                bot.stop()
