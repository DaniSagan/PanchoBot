from typing import Iterable, List


def index_of(obj_list: Iterable, obj: object) -> List[int]:
    return [i for i, item in enumerate(obj_list) if item == obj]


def first_index_of(obj_list: Iterable, obj: object) -> int:
    idx = [i for i, item in enumerate(obj_list) if item == obj]
    if len(idx) > 0:
        return idx[0]
    else:
        raise RuntimeError('Item {o} not found in iterable'.format(o=obj))
