from typing import Dict, List
import utils
from bot import MessageHandlerBase, BotBase, MessageStyle
from data import Message, ChatState


class ExchangeRates(MessageHandlerBase):
    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None):
        words = message.text.split(' ')  # type: List[str]
        if words[0].lower() == 'exchange':
            currencies = words[1:]
            rates_str = []
            for c1 in currencies:
                for c2 in currencies:
                    if c1 != c2:
                        rate = self.get_rate(c1, c2)
                        rates_str.append('{c1} to {c2}: {r}'.format(c1=c1, c2=c2, r=rate))
            bot.send_message(message.chat, '\n'.join(rates_str), MessageStyle.NONE)

    def get_rate(self, currency_1, currency_2) -> float:
        url = 'https://api.ratesapi.io/api/latest?base={c1}&symbols={c2}'.format(c1=currency_1.upper(), c2=currency_2.upper())  # type: str
        json_obj = utils.get_url_json(url)  # type: Dict
        return list(json_obj['rates'].values())[0]

