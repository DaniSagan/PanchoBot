from typing import Dict
import json


class JsonDeserializable(object):
    @classmethod
    def from_json(cls, json_object: Dict) -> 'JsonDeserializable':
        raise NotImplementedError()

    @classmethod
    def load_from_json_file(cls, filename: str) -> 'JsonDeserializable':
        with open(filename, 'r') as fobj:
            data = json.load(fobj)
        return cls.from_json(data)


class JsonSerializable(object):
    def to_json(self) -> Dict:
        raise NotImplementedError()

    def dump_to_json_file(self, filename: str):
        with open(filename, 'w') as fobj:
            json.dump(self.to_json(), fobj)