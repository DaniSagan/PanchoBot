import subprocess

from bot import MessageHandlerBase, BotBase
from data import Message


class PowerOff(MessageHandlerBase):
    def process_message(self, message: Message, bot: BotBase):
        words = message.text.split(' ')
        if words[0].lower() == 'cmd':
            if words[1].lower() == 'poweroff':
                subprocess.call(['shutdown', '-h', '1'])
                bot.send_message(message.chat, 'Apagando....')
                bot.stop()
