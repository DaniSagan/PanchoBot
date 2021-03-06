import sqlite3
from typing import Optional, List, Dict, Tuple, Set, Type, Any, Iterator
import itertools
import utils
from jsonutils import JsonDeserializable


class Column(object):
    TYPES = {
        "int": "INTEGER",
        "float": "REAL",
        "str": "TEXT",
        "bytes": "BLOB",
        "bool": "INTEGER"
    }

    def __init__(self):
        self.name = ''  # type: str
        self.type = ''  # type: str
        self.nullable = False  # type: bool

    def __eq__(self, other) -> bool:
        if isinstance(other, Column):
            return self.name == other.name and self.type == other.type and self.nullable == other.nullable
        else:
            return False

    @staticmethod
    def from_json(json_object: Dict) -> 'Column':
        res = Column()  # type: Column
        res.name = json_object['name']
        json_type = json_object['type']  # type: str
        res.type = Column.TYPES[json_type.replace('?', '')]
        res.nullable = json_type[-1] == '?'
        return res

    def __repr__(self):
        return 'Column: ' + self.name


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


class DataRow(object):
    def __init__(self, table_name: str, identity: object):
        self.identity = identity  # type: object
        self.table_name = table_name  # type: str
        self.items = {}  # type: Dict[str, object]

    def put(self, key: str, value: object) -> None:
        self.items[key] = value

    def get(self, key: str) -> Any:
        return self.items[key]


class DataTable(object):
    def __init__(self, table_name):
        self.table_name = table_name  # type: str
        self.rows = {}  # type: Dict[object, DataRow]

    def merge_rows(self, rows: List[DataRow]):
        for row in rows:
            if row.table_name == self.table_name and row.identity not in self.rows:
                self.rows[row.identity] = row

    def merge(self, other: 'DataTable'):
        if self.table_name == other.table_name:
            self.merge_rows(list(other.rows.values()))


class DataSet(object):
    def __init__(self):
        self.tables = {}  # type: Dict[str, DataTable]

    def merge_row(self, row: DataRow) -> None:
        if row.table_name not in self.tables:
            self.tables[row.table_name] = DataTable(row.table_name)
        self.tables[row.table_name].merge_rows([row])

    def merge(self, other: 'DataSet') -> None:
        for table_name in other.tables:
            if table_name not in self.tables:
                self.tables[table_name] = DataTable(table_name)
            self.tables[table_name].merge(other.tables[table_name])

    def add_column_to_table(self, table_name: str, column_name: str, value: object) -> None:
        table = self.tables[table_name]
        for row_key in table.rows:
            table.rows[row_key].put(column_name, value)


class Table(object):
    def __init__(self):
        self.name: str = 'table'
        self.columns: List[Column] = []
        self.primary_key: Optional[str] = None
        self.foreign_keys: List[ForeignKey] = []

    @staticmethod
    def from_json(json_object: Dict) -> 'Table':
        res: Table = Table()
        res.name = json_object.get('name', None)
        res.columns = [Column.from_json(r) for r in json_object['columns']]
        res.primary_key = json_object.get('primary_key')
        res.foreign_keys = [ForeignKey.from_json(fk) for fk in json_object['foreign_keys']]
        return res

    def get_create_cmd(self):
        columns_create_str_list: List[str] = []
        for column in self.columns:
            col_str: str = '{n} {t}'.format(n=column.name, t=column.type)
            if not column.nullable:
                col_str += ' NOT NULL'
            if self.primary_key is not None and self.primary_key == column.name:
                col_str += ' PRIMARY KEY'
            columns_create_str_list.append(col_str)
        foreign_key: ForeignKey
        for foreign_key in self.foreign_keys:
            fk_str: str = f'FOREIGN KEY ({foreign_key.column}) REFERENCES {foreign_key.referenced_table}({foreign_key.referenced_column})'
            columns_create_str_list.append(fk_str)
        res: str = f'CREATE TABLE IF NOT EXISTS [{self.name}] ({", ".join(columns_create_str_list)});'
        return res

    def row_to_tuple_for_insert(self, row: DataRow) -> Tuple:
        res: List = [None] * len(self.columns)
        key: str
        for key in row.items:
            try:
                index: int = [i for i, col in enumerate(self.columns) if key == col.name][0]
            except:
                raise RuntimeError('Column \'{k}\' not found in table \'{t}\''.format(k=key, t=self.name))
            res[index] = row.items[key]
        return tuple(res)

    def row_to_tuple_for_update(self, row: DataRow) -> Tuple:
        columns_without_pk: List[Column] = [c for c in self.columns if c.name != self.primary_key]
        res: List[object] = [None for _ in columns_without_pk]
        for key in row.items:
            if key != self.primary_key:
                try:
                    index: int = [i for i, col in enumerate(columns_without_pk) if key == col.name][0]
                except:
                    raise RuntimeError('Column \'{k}\' not found in table \'{t}\''.format(k=key, t=self.name))
                res[index] = row.items[key]
        res.append(row.items[self.primary_key])
        return tuple(res)

    def __repr__(self):
        return 'Table: ' + self.name


class DbSerializable(object):
    # def to_rows(self) -> List[DataRow]:
    #     raise NotImplementedError()

    def to_data_set(self) -> DataSet:
        raise NotImplementedError()

    @classmethod
    def from_data_set(cls, data_set: DataSet) -> List['DbSerializable']:
        raise NotImplementedError()


class Database(JsonDeserializable):
    def __init__(self):
        self.name: str = 'db'
        self.filename: Optional[str] = None
        self.tables: List[Table] = []

    @classmethod
    def from_json(cls, json_obj: Dict) -> 'Database':
        res: Database = Database()
        res.name = json_obj.get('name')
        res.filename = json_obj['filename']
        res.tables = [Table.from_json(t) for t in json_obj['tables']]
        return res

    def create_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.filename)

    def create_tables(self):
        conn: sqlite3.Connection = sqlite3.connect(self.filename)
        for table in self.tables:
            if not self.table_exists(conn, table.name):
                self.create_table(conn, table)
            else:
                self.update_table(conn, table)
        conn.close()

    def save(self, obj: DbSerializable):
        with self.create_connection() as connection:
            self.save_data_set(connection, obj.to_data_set())
            connection.commit()

    def table_exists(self, connection: sqlite3.Connection, table_name: str) -> bool:
        cursor: sqlite3.Cursor = connection.cursor()
        cursor.execute('SELECT name FROM sqlite_master WHERE type=\'table\' AND name=\'{t}\';'.format(t=table_name))
        rows: List = cursor.fetchall()
        return len(rows) > 0

    def create_table(self, connection: sqlite3.Connection, table: Table) -> None:
        cursor: sqlite3.Cursor = connection.cursor()
        cursor.execute(table.get_create_cmd())

    def update_table(self, connection: sqlite3.Connection, table: Table) -> None:
        # cursor = connection.cursor()
        curr_table = self.get_current_table(connection, table.name)
        update_needed: bool = False
        for curr_col in curr_table.columns:
            defined_col = utils.first_or_default_where(table.columns, lambda c: c.name == curr_col.name)
            if defined_col is not None and curr_col != defined_col:
                update_needed = True
        if update_needed:
            self.recreate_table(connection, table)
        else:
            # add_columns_needed = False  # type: bool
            for expected_column in table.columns:
                if expected_column not in curr_table.columns:
                    self.add_column_to_table(connection, table.name, expected_column)

    def recreate_table(self, connection: sqlite3.Connection, table: Table):
        curr_table: Table = self.get_current_table(connection, table.name)
        columns_str: str = ', '.join([c.name for c in curr_table.columns])
        cursor: sqlite3.Cursor = connection.cursor()
        backup_table_name: str = table.name + '_bk'
        sql_cmd = 'ALTER TABLE [{t}] RENAME TO [{bt}];'.format(t=table.name, bt=backup_table_name)
        cursor.execute(sql_cmd)
        cursor.execute(table.get_create_cmd())
        cursor.execute(
            'INSERT INTO [{t}]({c}) SELECT {c} FROM [{bt}];'.format(t=table.name, bt=backup_table_name, c=columns_str))
        cursor.execute('DROP TABLE [{bt}];'.format(bt=backup_table_name))

    def add_column_to_table(self, connection: sqlite3.Connection, table_name: str, column: Column) -> None:
        col_str: str = '[{n}] {t}'.format(n=column.name, t=column.type)
        if not column.nullable:
            col_str += ' NOT NULL'
        # if self.primary_key is not None and self.primary_key == column.name:
        #     col_str += ' PRIMARY KEY'
        sql_cmd: str = 'ALTER TABLE [{t}] ADD COLUMN {c}'.format(t=table_name, c=col_str)
        cursor: sqlite3.Cursor = connection.cursor()
        cursor.execute(sql_cmd)

    def get_current_table(self, connection: sqlite3.Connection, table_name: str) -> Table:
        res: Table = Table()
        res.name = table_name

        cursor: sqlite3.Cursor = connection.cursor()
        cursor.execute('PRAGMA table_info(\'{t}\');'.format(t=table_name))
        # cid_index = utils.first_index_where(cursor.description, lambda t: t[0] == 'cid')
        # name_index = utils.first_index_where(cursor.description, lambda t: t[0] == 'name')
        # type_index = utils.first_index_where(cursor.description, lambda t: t[0] == 'type')
        # notnull_index = utils.first_index_where(cursor.description, lambda t: t[0] == 'notnull')
        # pk_index = utils.first_index_where(cursor.description, lambda t: t[0] == 'pk')
        col_indices = Database.get_column_indices_from_cursor(cursor)
        row_tuples = cursor.fetchall()
        for row_tuple in row_tuples:
            column = Column()
            column.name = row_tuple[col_indices['name']]
            column.type = row_tuple[col_indices['type']]
            column.nullable = row_tuple[col_indices['notnull']] == 0
            res.columns.append(column)
        return res

    @staticmethod
    def get_column_indices_from_cursor(cursor: sqlite3.Cursor) -> Dict[str, int]:
        res: Dict[str, int] = {}
        for i, desc_tuple in enumerate(cursor.description):
            res[desc_tuple[0]] = i
        return res

    # def insert(self, obj: DbSerializable):
    #     dtc = obj.to_data_table_collection()
    #     conn = sqlite3.connect(self.filename)
    #     self.insert_data_table_collection(conn, dtc)
    #     conn.close()

    def save_data_set(self, connection: sqlite3.Connection, data_table_collection: DataSet) -> None:
        table_name: Table
        for table_name in data_table_collection.tables:
            self.save_data_table(connection, data_table_collection.tables[table_name])

    def save_data_table(self, connection: sqlite3.Connection, data_table: DataTable):
        existing_ids: Set = self.get_existing_ids(connection, data_table.table_name)
        new_rows: List[DataRow] = [r for r in data_table.rows.values() if r.identity not in existing_ids]
        self.insert_rows(connection, new_rows)
        existing_rows = [r for r in data_table.rows.values() if r.identity in existing_ids]
        self.update_rows(connection, existing_rows)

    def insert_rows(self, connection: sqlite3.Connection, rows: List[DataRow]) -> None:
        cursor: sqlite3.Cursor = connection.cursor()
        groups: Iterator[Tuple[str, Iterator[DataRow]]] = itertools.groupby(rows, lambda r: r.table_name)
        for table_name, table_rows in groups:
            table = [t for t in self.tables if t.name == table_name][0]  # type: Table
            columns = ', '.join([c.name for c in table.columns])  # type: str
            values_placeholder = ', '.join(['?' for _ in table.columns])  # type: str
            sql_cmd = 'INSERT into [{t}] ({c}) values ({v})'.format(t=table.name, c=columns,
                                                                    v=values_placeholder)  # type: str
            values = [table.row_to_tuple_for_insert(row) for row in table_rows]
            cursor.executemany(sql_cmd, values)

    def insert_data_set(self, connection: sqlite3.Connection, data_table_collection: DataSet):
        cursor = connection.cursor()
        for table_name in data_table_collection.tables:
            table = self.get_table(table_name)
            columns = ', '.join([c.name for c in table.columns])  # type: str
            values_placeholder = ', '.join(['?' for _ in table.columns])  # type: str
            sql_cmd = 'INSERT into [{t}] ({c}) values ({v})'.format(t=table.name, c=columns,
                                                                    v=values_placeholder)  # type: str
            values = [table.row_to_tuple_for_insert(row) for row in
                      data_table_collection.tables[table_name].rows.values()]
            cursor.executemany(sql_cmd, values)

    def update_rows(self, connection: sqlite3.Connection, rows: List[DataRow]) -> None:
        cursor = connection.cursor()  # type: sqlite3.Connection
        groups = itertools.groupby(rows, lambda r: r.table_name)
        for table_name, rows in groups:
            table = [t for t in self.tables if t.name == table_name][0]  # type: Table
            values = ', '.join([c.name + '=?' for c in table.columns if c.name != table.primary_key])  # type: str
            sql_cmd = 'UPDATE [{t}] SET {v} where {pk}=?'.format(t=table.name, pk=table.primary_key,
                                                                 v=values)  # type: str
            values = [table.row_to_tuple_for_update(row) for row in rows]
            cursor.executemany(sql_cmd, values)

    def table_contains(self, connection: sqlite3.Connection, table_name: str, obj_id: object):
        cursor = connection.cursor()  # type: sqlite3.Cursor
        table = self.get_table(table_name)  # type: Table
        cursor.execute('SELECT * FROM [{t}] WHERE {pk}=?;'.format(t=table_name, pk=table.primary_key), (obj_id,))
        rows = cursor.fetchall()
        return len(rows) > 0

    def get_table(self, table_name: str) -> Table:
        tables = [t for t in self.tables if t.name == table_name]
        if len(tables) > 0:
            return tables[0]
        else:
            raise RuntimeError('Table {t} not found'.format(t=table_name))

    def query(self, connection: sqlite3.Connection, table_name: str, id_object: object,
              include_children: bool) -> DataSet:
        res: DataSet = DataSet()
        dt: DataTable = DataTable(table_name)
        cursor: sqlite3.Cursor = connection.cursor()
        table: Table = self.get_table(table_name)
        column_names: List[str] = [c.name for c in table.columns]
        column_str: str = ', '.join(column_names)
        if id_object is not None:
            cursor.execute(
                f'SELECT {column_str} FROM [{table_name}] WHERE {table.primary_key}=?;',
                (id_object,))
        else:
            cursor.execute(f'SELECT {column_str} FROM [{table_name}];')
        row_tuples = cursor.fetchall()
        for row_tuple in row_tuples:
            row: DataRow = DataRow(table_name, row_tuple[utils.first_index_of(column_names, table.primary_key)])
            column_name: str
            for column_name in column_names:
                idx: List[int] = utils.index_of(column_names, column_name)
                if len(idx) > 0:
                    row.put(column_name, row_tuple[idx[0]])
            dt.merge_rows([row])
        res.tables[dt.table_name] = dt
        return res

    def raw_query(self, connection: sqlite3.Connection, table_name: str, column_list: List[str], where_clause: str,
                  query_params: Tuple) -> DataSet:
        table: Table = self.get_table(table_name)
        if table is None:
            raise ValueError(f'Table {table_name} is not defined')
        if table.primary_key not in column_list:
            column_list.insert(0, table.primary_key)
        cursor: sqlite3.Cursor = connection.cursor()
        if where_clause is None:
            query = f'SELECT {", ".join(column_list)} FROM [{table_name}]'
        else:
            query = f'SELECT {", ".join(column_list)} FROM [{table_name}] where {where_clause}'
        if query_params is None:
            cursor.execute(query)
        else:
            cursor.execute(query, query_params)
        row_tuples = cursor.fetchall()

        res: DataSet = DataSet()
        dt: DataTable = DataTable(table_name)
        for row_tuple in row_tuples:
            row: DataRow = DataRow(table_name, row_tuple[utils.first_index_of(column_list, table.primary_key)])
            for column_name in column_list:
                idx: List[int] = utils.index_of(column_list, column_name)
                if len(idx) > 0:
                    row.put(column_name, row_tuple[idx[0]])
            dt.merge_rows([row])
        res.tables[dt.table_name] = dt
        return res

    def query_row(self, connection: sqlite3.Connection, table_name: str, id_object: object) -> DataRow or None:
        ds = self.query(connection, table_name, id_object, True)
        dt = ds.tables[table_name]
        if len(dt.rows) > 0:
            return list(dt.rows.values())[0]
        else:
            return None

    def query_object(self, connection: sqlite3.Connection, obj_type: Type, table_name: str,
                     id_object: object) -> DbSerializable or None:
        ds = self.query(connection, table_name, id_object, True)
        dt = ds.tables[table_name]
        if len(dt.rows) == 0:
            return None
        ds = DataSet()
        ds.tables[dt.table_name] = dt
        return obj_type.from_data_set(ds)[0]

    def get_existing_ids(self, connection: sqlite3.Connection, table_name: str) -> Set:
        res = set()
        cursor = connection.cursor()  # type: sqlite3.Cursor
        table = self.get_table(table_name)  # type: Table
        cursor.execute('SELECT {c} FROM [{t}];'.format(c=table.primary_key, t=table_name))
        rows = cursor.fetchall()
        for row in rows:
            res.add(row[0])
        return res
