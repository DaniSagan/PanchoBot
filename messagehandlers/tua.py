import json
from typing import List, Dict

import time
from lxml.html import HtmlElement

import utils
from bot import MessageHandlerBase, BotBase, InlineKeyboardMarkup, InlineKeyboardButton
from data import Message, ChatState, CallbackQuery
from jsonutils import JsonSerializable, JsonDeserializable
from textformatting import MessageStyle, TextFormatter
from wordparser import WordParser
import re


class Stop(JsonSerializable, JsonDeserializable):
    def __init__(self):
        self.id_stop = 0  # type: int
        self.name = ''  # type: str

    def to_json(self) -> Dict:
        return {'id_stop': self.id_stop, 'name': self.name}

    @classmethod
    def from_json(cls, json_object: Dict) -> 'Stop':
        res = Stop()
        res.id_stop = json_object['id_stop']
        res.name = json_object['name']
        return res


class SubLine(JsonSerializable, JsonDeserializable):
    def __init__(self):
        self.id_sub_line = ''  # type: str
        self.name = ''  # type: str
        self.stops = []  # type: List[Stop]

    def to_json(self) -> Dict:
        return {
            'id_sub_line': self.id_sub_line,
            'name': self.name,
            'stops': [s.to_json() for s in self.stops]
        }

    @classmethod
    def from_json(cls, json_object: Dict) -> 'JsonDeserializable':
        res = SubLine()  # type: SubLine
        res.id_sub_line = json_object['id_sub_line']
        res.name = json_object['name']
        res.stops = [Stop.from_json(j) for j in json_object['stops']]
        return res


class Line(JsonSerializable, JsonDeserializable):

    def __init__(self):
        self.name = ''
        self.sub_line_forth = None  # type: SubLine
        self.sub_line_back = None  # type: SubLine
        self.schedule = ''  # type: str

    def to_json(self) -> Dict:
        return {
            'name': self.name,
            'sub_line_forth': self.sub_line_forth.to_json(),
            'sub_line_back': self.sub_line_back.to_json(),
            'schedule': self.schedule
        }

    @classmethod
    def from_json(cls, json_object: Dict) -> 'Line':
        res = Line()  # type: Line
        res.name = json_object['name']
        res.sub_line_forth = SubLine.from_json(json_object['sub_line_forth'])
        res.sub_line_back = SubLine.from_json(json_object['sub_line_back'])
        res.schedule = json_object['schedule']
        return res

    def __repr__(self):
        return self.name.upper()


class TuaLines(JsonSerializable, JsonDeserializable):
    LINE_NAMES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'o', 'buho']

    def __init__(self):
        self.lines = []  # type: List[Line]

    @classmethod
    def from_json(cls, json_object: Dict) -> 'TuaLines':
        res = TuaLines()  # type: TuaLines
        res.lines = [Line.from_json(j) for j in json_object['lines']]
        return res

    def to_json(self) -> Dict:
        return {'lines': [l.to_json() for l in self.lines]}

    def get_sub_line(self, sub_line_name: str):
        line = utils.first_or_default_where(self.lines, lambda l: l.sub_line_forth.id_sub_line == sub_line_name or l.sub_line_back.id_sub_line == sub_line_name)  # type: Line
        if line is not None:
            if line.sub_line_forth.id_sub_line == sub_line_name:
                return line.sub_line_forth
            else:
                return line.sub_line_back


class EstimationItem(JsonDeserializable):
    def __init__(self):
        self.destination = ''  # type: str
        self.meters = 0  # type: int
        self.seconds = ''  # type: int

    @classmethod
    def from_json(cls, json_object: Dict) -> 'EstimationItem':
        if json_object is None:
            return None
        res = EstimationItem()
        res.destination = json_object['destino']
        res.meters = json_object['meters']
        res.seconds = json_object['seconds']
        return res


class Estimation(JsonDeserializable):
    def __init__(self):
        self.line = ''  # type: str
        self.vh_first = None  # type: EstimationItem
        self.vh_second = None  # type: EstimationItem

    @classmethod
    def from_json(cls, json_object: Dict) -> 'Estimation':
        res = Estimation()  # type: Estimation
        res.line = json_object['line']
        res.vh_first = EstimationItem.from_json(json_object['vh_first'])
        res.vh_second = EstimationItem.from_json(json_object['vh_second'])
        return res


class TuaHandler(MessageHandlerBase):
    @staticmethod
    def get_help() -> TextFormatter:
        res = TextFormatter()
        res.italic('\U00002328 Tua lines').new_line().normal('Show all lines.').new_line().new_line()
        res.italic('\U00002328 Tua line <line>').new_line().normal('Show all stops for <line>.').new_line().new_line()
        res.italic('\U00002328 Tua update').new_line().normal('Update line info.')
        return res

    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None):
        if chat_state is None:
            word_parser = WordParser.from_str('cmd:w action:w')
            res = word_parser.match(message.text)
            if res.success:
                if res.results['cmd'].lower() == 'tua':
                    if res.results['action'].lower() == 'update':
                        self.retrieve_data()
                        bot.send_message(message.chat, 'Lines updated!', MessageStyle.NONE)
                    elif res.results['action'].lower() == 'lines':
                        self.show_lines(message, bot)
                    elif res.results['action'].lower() == 'line':
                        parameters = message.text.split(' ')[2:]
                        if len(parameters) > 0:
                            self.show_line(message, bot, parameters[0])

    def process_callback_query(self, callback_query: CallbackQuery, bot: BotBase, chat_state: ChatState = None):
        if chat_state.data['action'] == 'line':
            self.show_estimation(callback_query, bot, chat_state)

    def retrieve_data(self):
        lines_json = {'lines': []}
        for line in TuaLines.LINE_NAMES:
            lines_json['lines'].append(self.retrieve_line(line).to_json())
        with open('dat/app/tua/lines.json', 'w') as fobj:
            json.dump(lines_json, fobj, indent=4)

    def retrieve_line(self, name: str) -> Line:
        res = Line()
        res.name = name
        # url = 'http://www.tua.es/es/lineas-y-horarios/linea-{n}.html#paradasIda'.format(n=name)
        # html = utils.get_url_html(url)

        html = utils.get_file_html('dat/app/tua/linea-{n}.html'.format(n=name))  # type: HtmlElement

        sub_line_forth_html = html.xpath('//div[@id="ida"]/div[@class="caja-scroll"]/div')[0]
        sub_line_forth = SubLine()
        sub_line_forth.id_sub_line = name.upper() + '1'
        sub_line_forth.name = utils.html_strip_str(sub_line_forth_html.xpath('p[@class="nombre-linea"]/strong')[0].text)
        sub_line_forth_stops_html = sub_line_forth_html.xpath('ul[@class="paradas"]/li/a')
        for stop_html in sub_line_forth_stops_html:
            stop = Stop()
            stop.id_stop = int(stop_html.xpath('span')[0].text)
            stop.name = stop_html.xpath('strong')[0].text
            sub_line_forth.stops.append(stop)
        res.sub_line_forth = sub_line_forth

        sub_line_back_html = html.xpath('//div[@id="vuelta"]/div[@class="caja-scroll"]/div')[0]
        sub_line_back = SubLine()
        sub_line_back.id_sub_line = name.upper() + '2'
        sub_line_back.name = utils.html_strip_str(sub_line_back_html.xpath('p[@class="nombre-linea"]/strong')[0].text)
        sub_line_back_stops_html = sub_line_back_html.xpath('ul[@class="paradas"]/li/a')
        for stop_html in sub_line_back_stops_html:
            stop = Stop()
            stop.id_stop = int(stop_html.xpath('span')[0].text)
            stop.name = stop_html.xpath('strong')[0].text
            sub_line_back.stops.append(stop)
        res.sub_line_back = sub_line_back

        # line_info_html = html.xpath('//div[@class="ficha-linea"]')[0]
        # line_name_html = line_info_html.xpath('//div[@class="tabs2"]/ul/li')

        schedule_html = html.xpath('//div[@class="tabla-horarios"]/div[@class="modulo100"]')  # type: List[HtmlElement]
        res.schedule = '\n\n'.join([utils.html_strip_str(t.text_content()) for t in schedule_html])

        return res

    def show_lines(self, message: Message, bot: BotBase) -> None:
        tua_lines = TuaLines.load_from_json_file('dat/app/tua/lines.json')  # type: TuaLines
        fmt = TextFormatter()
        for line in tua_lines.lines:
            fmt.bold(line.sub_line_forth.id_sub_line + ': ').normal(line.sub_line_forth.name + '\n')
            fmt.bold(line.sub_line_back.id_sub_line + ': ').normal(line.sub_line_back.name + '\n')
            fmt.normal('\n')
        bot.send_message(message.chat, fmt, MessageStyle.MARKDOWN)

    def show_line(self, message: Message, bot: BotBase, line_name: str) -> None:
        tua_lines = TuaLines.load_from_json_file('dat/app/tua/lines.json')  # type: TuaLines
        sub_line = tua_lines.get_sub_line(line_name.upper())  # type: SubLine
        if sub_line is not None:
            keyboard = InlineKeyboardMarkup()  # type: InlineKeyboardMarkup
            for stop in sub_line.stops:
                button = InlineKeyboardButton()
                button.text = str(stop.id_stop) + ' - ' + stop.name
                button.callback_data = stop.id_stop
                keyboard.inline_keyboard.append([button])
            msg = '{id} - {name}\nSelect stop:'.format(id=sub_line.id_sub_line, name=sub_line.name)
            bot.send_message_with_inline_keyboard(message.chat, msg, MessageStyle.NONE, keyboard)

            chat_state = ChatState()
            chat_state.chat_id = message.chat.id_chat
            chat_state.current_handler_name = self.handler_name
            chat_state.last_time = time.time()
            chat_state.data = {'action': 'line', 'id_sub_line': sub_line.id_sub_line}

            message.chat.save_chat_state(chat_state)

        else:
            bot.send_message(message.chat, 'Line {} not found'.format(line_name), MessageStyle.NONE)

    def show_estimation(self, callback_query: CallbackQuery, bot: BotBase, chat_state: ChatState):
        id_stop = int(callback_query.data)  # type: int
        estimations = self.get_estimations(id_stop)  # type: List[Estimation]
        fmt = TextFormatter()  # type: TextFormatter
        for estimation in estimations:
            fmt.bold('Line ' + estimation.line).new_line()
            if estimation.vh_first is not None:
                fmt.normal('1st {}'.format(estimation.vh_first.destination)).new_line()
                fmt.normal('    {}'.format(utils.seconds_to_duration(estimation.vh_first.seconds))).new_line()
                fmt.normal('    {} meters'.format(estimation.vh_first.meters)).new_line()
            if estimation.vh_second is not None:
                fmt.normal('2nd {}'.format(estimation.vh_second.destination)).new_line()
                fmt.normal('    {}'.format(utils.seconds_to_duration(estimation.vh_second.seconds))).new_line()
                fmt.normal('    {} meters'.format(estimation.vh_second.meters)).new_line()
        bot.send_message(callback_query.message.chat, fmt, MessageStyle.MARKDOWN)

    def get_estimations(self, id_stop: int) -> List[Estimation]:
        url = 'http://www.tua.es/rest/estimaciones/' + str(id_stop)
        json_obj = utils.get_url_json(url)
        return [Estimation.from_json(j) for j in json_obj['estimaciones']['value']['publicEstimation']]
