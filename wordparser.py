from enum import Enum
from typing import Dict
from typing import List
from typing import Tuple


class ParserType(Enum):
    NONE = 0
    WORD = 1
    INTEGER = 2
    FLOAT = 3
    BOOL = 4
    TIME_INTERVAL = 5


class GroupQuantityType(Enum):
    SINGLE = 0
    LIST = 1
    ANY = 2


class ParserGroup(object):

    TYPES = {'w': ParserType.WORD, 'n': ParserType.INTEGER, 'f': ParserType.FLOAT, 'b': ParserType.BOOL, 't': ParserType.TIME_INTERVAL}

    def __init__(self):
        self.name = ''  # type: str
        self.type = ParserType.NONE  # type: ParserType
        self.quantity = 0  # type: int
        self.quantity_type = GroupQuantityType.SINGLE  # type: GroupQuantityType

    @staticmethod
    def from_str(s: str) -> 'ParserGroup':
        res = ParserGroup()
        try:
            data = s.split(':')
            res.name = data[0]
            group_def = data[1]
            if len(group_def) == 1:
                res.type = ParserGroup.TYPES[group_def]
                res.quantity = 1
                res.quantity_type = GroupQuantityType.SINGLE
            elif len(group_def) >= 2:
                res.type = ParserGroup.TYPES[group_def[-1]]
                if group_def[0] == '*':
                    res.quantity = 2**32
                    res.quantity_type = GroupQuantityType.ANY
                else:
                    res.quantity = int(group_def[:-1])
                    res.quantity_type = GroupQuantityType.LIST
            return res
        except:
            raise ValueError('Incorrect value for group: {0}'.format(s))

    def __eq__(self, other):
        if not isinstance(other, ParserGroup):
            return False
        else:
            return self.name == other.name and self.type == other.type and self.quantity == other.quantity


class MatchResult(object):
    def __init__(self):
        self.success = False  # type: bool
        self.results = {}  # Dict[str, str]


class WordParser(object):

    INTERVALS = {'d': 86400., 'h': 3600., 'm': 60., 's': 1.}  # type: Dict[str, float]

    def __init__(self):
        self.groups = []  # type: List[ParserGroup]

    @staticmethod
    def from_str(s: str) -> 'WordParser':
        res = WordParser()
        res.groups = list(map(ParserGroup.from_str, s.split(' ')))
        return res

    def match(self, s: str) -> MatchResult:
        res = MatchResult()
        words = s.split(' ')
        curr_word_index = 0
        try:
            for group in self.groups:
                if group.quantity_type == GroupQuantityType.SINGLE:
                    if group.type == ParserType.WORD:
                        value = words[curr_word_index]
                    elif group.type == ParserType.INTEGER:
                        value = int(words[curr_word_index])
                    elif group.type == ParserType.FLOAT:
                        value = float(words[curr_word_index])
                    elif group.type == ParserType.BOOL:
                        value = bool(words[curr_word_index])
                    elif group.type == ParserType.TIME_INTERVAL:
                        value = WordParser.parse_time_interval(words[curr_word_index])
                    curr_word_index += 1
                    res.results[group.name] = value
                elif group.quantity_type == GroupQuantityType.LIST:
                    value = []
                    for k in range(group.quantity):
                        if group.type == ParserType.WORD:
                            value.append(words[curr_word_index])
                        elif group.type == ParserType.INTEGER:
                            value.append(int(words[curr_word_index]))
                        elif group.type == ParserType.FLOAT:
                            value.append(float(words[curr_word_index]))
                        elif group.type == ParserType.BOOL:
                            value.append(bool(words[curr_word_index]))
                        elif group.type == ParserType.TIME_INTERVAL:
                            value.append(WordParser.parse_time_interval(words[curr_word_index]))
                        curr_word_index += 1
                    res.results[group.name] = value
                elif group.quantity_type == GroupQuantityType.ANY:
                    value = []
                    while curr_word_index < len(words):
                        if group.type == ParserType.WORD:
                            value.append(words[curr_word_index])
                        elif group.type == ParserType.INTEGER:
                            value.append(int(words[curr_word_index]))
                        elif group.type == ParserType.FLOAT:
                            value.append(float(words[curr_word_index]))
                        elif group.type == ParserType.BOOL:
                            value.append(bool(words[curr_word_index]))
                        elif group.type == ParserType.TIME_INTERVAL:
                            value.append(WordParser.parse_time_interval(words[curr_word_index]))
                        curr_word_index += 1
                    res.results[group.name] = value
            res.success = True
        except ValueError:
            res.success = False
        except IndexError:
            res.success = False
        except Exception:
            res.success = False
        return res

    @staticmethod
    def parse_time_interval(s: str) -> float:
        acc_number = ''
        acc_unit = ''
        groups = []  # type: List[Tuple[int, str]]
        for c in s:
            if c.isdigit():
                if acc_unit != '':
                    groups.append((int(acc_number), acc_unit))
                    acc_number = ''
                    acc_unit = ''
                acc_number += c
            else:
                acc_unit += c
        groups.append((int(acc_number), acc_unit))
        res = 0.  # type: float
        for group in groups:
            res += WordParser.INTERVALS[group[1]] * group[0]
        return res

