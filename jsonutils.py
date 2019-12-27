from typing import Dict


class JsonDeserializable(object):
    @staticmethod
    def from_json(json_object: Dict) -> object:
        raise NotImplementedError()
