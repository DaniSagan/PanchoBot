import sqlite3
from typing import Optional, List


class Column(object):
    def __init__(self):
        self.name = None  # type: Optional[str]
        self.type = None  # type: Optional[str]

    @staticmethod
    def from_json(json_object) -> 'Column':
        res = Column()
        res.name = json_object['name']
        res.type = json_object['type']
        return res


class Table(object):
    def __init__(self):
        self.name = 'table'  # type: str
        self.columns = []  # type: List[Column]

    @staticmethod
    def from_json(json_object) -> 'Table':
        res = Table()  # type: Table
        res.name = json_object.get('name', None)
        res.filename = json_object['filename']
        res.columns = [Column.from_json(r) for r in json_object['columns']]
        return res


class Database(object):
    def __init__(self):
        self.name = 'db'  # type: str
        self.filename = None  # type: Optional[str]
        self.tables = []  # type: List[Table]

    @staticmethod
    def from_json(json) -> 'Database':
        res = Database()  # type: Database
        res.name = json['name']
        res.tables = [Table.from_json(t) for t in json['tables']]
        return res

    def create_tables(self):
        conn = sqlite3.connect(self.filename)  # type: sqlite3.Connection
        cursor = conn.cursor()  # type: sqlite3.Cursor
        for table in self.tables:
            self.create_table(cursor, table)

    def create_table(self, cursor: sqlite3.Cursor, table: Table):
        sql_cmd = 'CREATE TABLE IF NOT EXISTS {t} ()'


