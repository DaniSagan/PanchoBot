import sqlite3
from typing import Optional, List, Dict


class Column(object):
    TYPES = {
        "int": "INTEGER",
        "float": "REAL",
        "str": "TEXT",
        "bytes": "BLOB",
        "bool": "INTEGER"
    }

    def __init__(self):
        self.name = None  # type: Optional[str]
        self.type = None  # type: Optional[str]
        self.nullable = False  # type: bool

    @staticmethod
    def from_json(json_object: Dict) -> 'Column':
        res = Column()  # type: Column
        res.name = json_object['name']
        json_type = json_object['type']  # type: str
        res.type = json_type.replace('?', '')
        res.nullable = json_type[-1] == '?'
        return res


class ForeignKey(object):
    def __init__(self):
        self.column = ''
        self.referenced_table = ''
        self.referenced_column = ''

    @staticmethod
    def from_json(json_object: Dict) -> 'ForeignKey':
        res = ForeignKey()  # type: ForeignKey
        res.column = json_object['column']
        references = json_object['references'].split('.')  # type: List[str]
        res.referenced_table = references[0]
        res.referenced_column = references[1]
        return res


class Table(object):
    def __init__(self):
        self.name = 'table'  # type: str
        self.columns = []  # type: List[Column]
        self.primary_key = None  # type: Optional[str]
        self.foreign_keys = []  # type: List[ForeignKey]

    @staticmethod
    def from_json(json_object: Dict) -> 'Table':
        res = Table()  # type: Table
        res.name = json_object.get('name', None)
        res.columns = [Column.from_json(r) for r in json_object['columns']]
        res.primary_key = json_object.get('primary_key')
        res.foreign_keys = [ForeignKey.from_json(fk) for fk in json_object['foreign_keys']]
        return res

    def get_create_cmd(self):
        columns_create_str_list = []  # type: List[str]
        for column in self.columns:
            col_str = '{n} {t}'.format(n=column.name, t=Column.TYPES[column.type])  # type: str
            if not column.nullable:
                col_str += ' NOT NULL'
            if self.primary_key is not None and self.primary_key == column.name:
                col_str += ' PRIMARY KEY'
            columns_create_str_list.append(col_str)
        for foreign_key in self.foreign_keys:
            fk_str = 'FOREIGN KEY ({c}) REFERENCES {rt}({rc})'.format(c=foreign_key.column, rt=foreign_key.referenced_table, rc=foreign_key.referenced_column)
            columns_create_str_list.append(fk_str)
        res = 'CREATE TABLE IF NOT EXISTS {t} ({cols});'.format(t=self.name, cols=', '.join(columns_create_str_list))
        return res


class RowItem(object):
    def __init__(self, key: str, value: object):
        self.key = key  # type: str
        self.value = value  # type: object


class Row(object):
    def __init__(self):
        self.items = []  # type: List[RowItem]
        self.table_name = ''  # type: str

    def put(self, key: str, value: object) -> None:
        self.items.append(RowItem(key, value))


class Database(object):
    def __init__(self):
        self.name = 'db'  # type: str
        self.filename = None  # type: Optional[str]
        self.tables = []  # type: List[Table]

    @staticmethod
    def from_json(json: Dict) -> 'Database':
        res = Database()  # type: Database
        res.name = json.get('name')
        res.filename = json['filename']
        res.tables = [Table.from_json(t) for t in json['tables']]
        return res

    def create_tables(self):
        conn = sqlite3.connect(self.filename)  # type: sqlite3.Connection
        for table in self.tables:
            if not self.table_exists(conn, table.name):
                self.create_table(conn, table)
        conn.close()

    def table_exists(self, connection: sqlite3.Connection, table_name: str) -> bool:
        cursor = connection.cursor()  # type: sqlite3.Cursor
        cursor.execute('SELECT name FROM sqlite_master WHERE type=\'table\' AND name=\'{t}\';'.format(t=table_name))
        rows = cursor.fetchall()
        return len(rows) > 0

    def create_table(self, connection: sqlite3.Connection, table: Table):
        cursor = connection.cursor()  # type: sqlite3.Cursor
        cursor.execute(table.get_create_cmd())

