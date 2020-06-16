import http.client
import json
import urllib.request
import urllib.parse
import socket
from typing import Iterable, List, Dict, Callable, TypeVar
import re

import lxml.html


def index_of(obj_list: Iterable, obj: object) -> List[int]:
    return [i for i, item in enumerate(obj_list) if item == obj]


def first_index_of(obj_list: Iterable, obj: object) -> int:
    idx: List[int] = [i for i, item in enumerate(obj_list) if item == obj]
    if len(idx) > 0:
        return idx[0]
    else:
        raise RuntimeError('Item {o} not found in iterable'.format(o=obj))


def first_index_where(obj_list: Iterable, fn: Callable[[object], bool]) -> int:
    idx: List[int] = [i for i, item in enumerate(obj_list) if fn(item)]
    if len(idx) > 0:
        return idx[0]
    else:
        raise RuntimeError('Item not found in iterable')


T = TypeVar('T')


def first_where(obj_list: Iterable[T], fn: Callable[[T], bool]) -> T:
    items: List[T] = [item for i, item in enumerate(obj_list) if fn(item)]
    if len(items) > 0:
        return items[0]
    else:
        raise RuntimeError('Item not found in iterable')


def first_or_default_where(obj_list: Iterable[T], fn: Callable[[T], bool]) -> T:
    items: List[T] = [item for i, item in enumerate(obj_list) if fn(item)]
    if len(items) > 0:
        return items[0]
    else:
        return None


def get_url_html(url: str, params: Dict = None) -> lxml.html.HtmlElement:
    headers: Dict[str, str] = {"User-Agent": "Mozilla/5.0"}
    if params is not None:
        req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode('ascii'), headers=headers)
    else:
        req = urllib.request.Request(url, headers=headers)
    response: http.client.HTTPResponse
    with urllib.request.urlopen(req) as response:
        if response.status == 200:
            received_bytes: bytes = response.read()
            received_str: str = received_bytes.decode("utf8")
        else:
            raise RuntimeError(f'Could get url {url}. Reason: {response.reason}')

    # noinspection PyUnboundLocalVariable
    print('Received response: {r}'.format(r=received_str))
    parser = lxml.html.HTMLParser()
    return lxml.html.document_fromstring(received_str, parser=parser)


def get_file_html(filename: str) -> lxml.html.HtmlElement:
    fobj: http.client.HTTPResponse
    with open(filename, 'r') as fobj:
        file_contents: bytes = fobj.read()
    parser = lxml.html.HTMLParser()
    return lxml.html.document_fromstring(file_contents, parser=parser)


def get_url_json(url: str, params: Dict = None) -> Dict:
    headers: Dict[str, str] = {"User-Agent": "Mozilla/5.0"}
    if params is not None:
        req: urllib.request.Request = urllib.request.Request(url,
                                                             data=urllib.parse.urlencode(params).encode('ascii'),
                                                             headers=headers)
    else:
        req = urllib.request.Request(url, headers=headers)
    response: http.client.HTTPResponse
    with urllib.request.urlopen(req) as response:
        if response.status == 200:
            received_bytes: bytes = response.read()
            received_str: str = received_bytes.decode("utf8")
        else:
            raise RuntimeError(f'Could get url {url}. Reason: {response.reason}')

    # noinspection PyUnboundLocalVariable
    print(f'Received response: {received_str}')
    return json.loads(received_str)


def get_file_json(filename: str) -> Dict:
    res: Dict or None = None
    with open(filename) as fobj:
        res = json.loads(fobj.read().strip())
    return res


def dict_to_url_params(value: Dict) -> Dict:
    res: Dict = {}
    for key in value:
        if isinstance(value[key], dict):
            res[key] = json.dumps(value[key])
        else:
            res[key] = value[key]
    return res


def html_strip_str(s: str) -> str:
    return re.sub(r'\s\s+', ' ', s.replace('\n', '')).strip()


def seconds_to_duration(s: int) -> str:
    days: int = s // 86400
    hours: int = (s // 3600) % 24
    minutes: int = (s // 60) % 60
    seconds: int = s % 60
    res: str = ''
    if days > 0:
        res += f'{days}d'
    if hours > 0:
        res += f'{hours}h'
    if minutes > 0:
        res += f'{minutes}m'
    if seconds > 0 or not res:
        res += f'{seconds}s'
    return res


def is_float(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def get_ip_address() -> str:
    s: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

# 'cmd:w num:n msg:*w'
# def parse_words(input_str: str, word_group_str: str) -> Dict[str, object]:
#     words = list(map(str.lower, input_str.split(' ')))
#     word_groups = word_group_str.split(' ')
#     for word_group in word_groups:

