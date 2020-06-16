from typing import Dict, List
import utils
from bot.base import MessageHandlerBase, BotBase
from data import Message, ChatState
from textformatting import TextFormatter, MessageStyle


class ExchangeRatesMessageHandler(MessageHandlerBase):
    @staticmethod
    def get_help() -> TextFormatter:
        res: TextFormatter = TextFormatter()
        res.inline_code('\U00002328 Exchange <amount> <currency1> <currency2>...').new_line().normal(
            'Get value of <amount> between different conversions.').new_line().new_line()
        res.normal('Examples:').new_line()
        res.italic('Exchange 100 gbp eur').new_line()
        res.italic('Exchange eur usd gbp').new_line()
        return res

    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None):
        words: List[str] = message.text.split(' ')
        if words[0].lower() == 'exchange':
            if utils.is_float(words[1]):
                amount: float or None = float(words[1])
                currencies: List[str] = words[2:]
            else:
                amount: float or None = None
                currencies = words[1:]
            rates_str: List[str] = []
            c1: str
            for c1 in currencies:
                c2: str
                for c2 in currencies:
                    if c1 != c2:
                        rate: float = self.get_rate(c1, c2)
                        rates_str.append('{c1} to {c2}: {r}'.format(c1=c1, c2=c2, r=rate))
                        if amount is not None:
                            rates_str.append(f'{amount:.2f} {c1} = {rate * amount:.2f} {c2}')
            bot.send_message(message.chat, '\n'.join(rates_str), MessageStyle.NONE)

    def get_rate(self, currency_1, currency_2) -> float:
        url: str = f'https://api.ratesapi.io/api/latest?base={currency_1.upper()}&symbols={currency_2.upper()}'
        json_obj = utils.get_url_json(url)  # type: Dict
        return list(json_obj['rates'].values())[0]

