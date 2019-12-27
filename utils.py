import http.client
import json
import urllib.request
import urllib.parse
from typing import Iterable, List, Dict, Callable


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


def dict_to_url_params(value: Dict) -> str:
    res = {}
    for key in value:
        if isinstance(value[key], dict):
            res[key] = json.dumps(value[key])
        else:
            res[key] = value[key]
    return res
