import http.client
import json
import urllib.request
import urllib.parse
from typing import Iterable, List, Dict, Callable
import re

import lxml.html


def index_of(obj_list: Iterable, obj: object) -> List[int]:
    return [i for i, item in enumerate(obj_list) if item == obj]


def first_index_of(obj_list: Iterable, obj: object) -> int:
    idx = [i for i, item in enumerate(obj_list) if item == obj]
    if len(idx) > 0:
        return idx[0]
    else:
        raise RuntimeError('Item {o} not found in iterable'.format(o=obj))


def first_index_where(obj_list: Iterable, fn: Callable[[object], bool]) -> int:
    idx = [i for i, item in enumerate(obj_list) if fn(item)]
    if len(idx) > 0:
        return idx[0]
    else:
        raise RuntimeError('Item not found in iterable')


def first_where(obj_list: Iterable, fn: Callable[[object], bool]) -> object:
    items = [item for i, item in enumerate(obj_list) if fn(item)]
    if len(items) > 0:
        return items[0]
    else:
        raise RuntimeError('Item not found in iterable')


def first_or_default_where(obj_list: Iterable, fn: Callable[[object], bool]) -> object:
    items = [item for i, item in enumerate(obj_list) if fn(item)]
    if len(items) > 0:
        return items[0]
    else:
        return None


def get_url_html(url: str, params: Dict = None) -> lxml.html.HtmlElement:
    headers = {"User-Agent": "Mozilla/5.0"}
    if params is not None:
        req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode('ascii'), headers=headers)
    else:
        req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:  # type:  http.client.HTTPResponse
        if response.status == 200:
            received_bytes = response.read()  # type: bytes
            received_str = received_bytes.decode("utf8")  # type: str
        else:
            raise RuntimeError('Could get url {url}. Reason: {r}'.format(url=url, r=response.reason))

    # noinspection PyUnboundLocalVariable
    print('Received response: {r}'.format(r=received_str))
    parser = lxml.html.HTMLParser()
    return lxml.html.document_fromstring(received_str, parser=parser)


def get_file_html(filename: str) -> lxml.html.HtmlElement:
    with open(filename, 'r') as fobj:  # type:  http.client.HTTPResponse
        file_contents = fobj.read()  # type: bytes
    parser = lxml.html.HTMLParser()
    return lxml.html.document_fromstring(file_contents, parser=parser)


def get_url_json(url: str, params: Dict = None) -> Dict:
    headers = {"User-Agent": "Mozilla/5.0"}
    if params is not None:
        req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode('ascii'), headers=headers)
    else:
        req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:  # type:  http.client.HTTPResponse
        if response.status == 200:
            received_bytes = response.read()  # type: bytes
            received_str = received_bytes.decode("utf8")  # type: str
        else:
            raise RuntimeError('Could get url {url}. Reason: {r}'.format(url=url, r=response.reason))

    # noinspection PyUnboundLocalVariable
    print('Received response: {r}'.format(r=received_str))
    return json.loads(received_str)


def get_file_json(filename: str) -> Dict:
    res = None  # type: Dict
    with open(filename) as fobj:
        res = json.loads(fobj.read().strip())
    return res


def dict_to_url_params(value: Dict) -> Dict:
    res = {}
    for key in value:
        if isinstance(value[key], dict):
            res[key] = json.dumps(value[key])
        else:
            res[key] = value[key]
    return res


def html_strip_str(s: str) -> str:
    return re.sub(r'\s\s+', ' ', s.replace('\n', '')).strip()


def seconds_to_duration(s: int) -> str:
    days = s // 86400
    hours = (s // 3600) % 24
    minutes = (s // 60) % 60
    seconds = s % 60
    res = ''
    if days > 0:
        res += '{}d'.format(days)
    if hours > 0:
        res += '{}h'.format(hours)
    if minutes > 0:
        res += '{}m'.format(minutes)
    if seconds > 0 or not res:
        res += '{}s'.format(seconds)
    return res

# 'cmd:w num:n msg:*w'
# def parse_words(input_str: str, word_group_str: str) -> Dict[str, object]:
#     words = list(map(str.lower, input_str.split(' ')))
#     word_groups = word_group_str.split(' ')
#     for word_group in word_groups:

