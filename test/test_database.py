import unittest

import pathlib
from typing import Dict, Any, Union, List
from typing import List

import sqlite3

import utils
from db.database import Database, DbSerializable, DataSet, DataRow, DataTable, Table, Column

TABLE_PARENT: str = 'table_parent'
TABLE_CHILD: str = 'table_child'


class ChildObject(DbSerializable):
    def __init__(self):
        self.id_table_child: int = 0
        self.value_1: str = ''

    @classmethod
    def from_data_set(cls, data_set: DataSet) -> List['DbSerializable']:
        pass

    def to_data_set(self) -> DataSet:
        ds: DataSet = DataSet()
        row = DataRow(TABLE_CHILD, self.id_table_child)
        row.put('id_table_child', self.id_table_child)
        row.put('value_1', self.value_1)
        ds.merge_row(row)
        return ds


class ParentObject(DbSerializable):
    def __init__(self):
        self.id_table_parent: int = 0
        self.value_1: str = ''
        self.children: List[ChildObject] = []

    def to_data_set(self) -> DataSet:
        ds: DataSet = DataSet()
        row: DataRow = DataRow(TABLE_PARENT , self.id_table_parent)
        row.put('id_table_parent', self.id_table_parent)
        row.put('value_1', self.value_1)
        ds.merge_row(row)
        child: ChildObject
        for child in self.children:
            child_ds: DataSet = child.to_data_set()
            child_ds.add_column_to_table(TABLE_CHILD, 'id_table_parent', self.id_table_parent)
            ds.merge(child_ds)
        return ds

    @classmethod
    def from_data_set(cls, data_set: DataSet) -> List['ParentObject']:
        res: List[ParentObject] = []
        table: DataTable = data_set.tables[TABLE_PARENT]
        row_key: DataRow
        for row_key in table.rows:
            obj: ParentObject = ParentObject()
            obj.id_table_parent = table.rows[row_key].get('id_table_parent')
            obj.value_1 = table.rows[row_key].get('value_1')
            res.append(obj)
        return res


class TestDatabase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        db_file: pathlib.Path = pathlib.Path('test.sqlite')
        if db_file.exists():
            db_file.unlink()

    def test_from_json(self):
        db_json: Dict = utils.get_file_json('testfiles/db_definition.json')
        db: Database = Database.from_json(db_json)
        self.assertEqual(len(db.tables), 2)
        try:
            parent_table: Table = db.get_table(TABLE_PARENT)
            child_table: Table = db.get_table('table_child')
        except RuntimeError:
            self.fail("get_table() raised RuntimeError unexpectedly!")
        columns: List[str] = ['id_table_parent', 'value_1']
        try:
            column_name: str
            for column_name in columns:
                col: Column = utils.first_where(parent_table.columns, lambda c: c.name == column_name)
        except RuntimeError:
            self.fail(f'Column {column_name} not found in table {TABLE_PARENT}')
        columns = ['id_table_child', 'id_table_parent', 'value_1']
        try:
            for column_name in columns:
                col = utils.first_where(child_table.columns, lambda c: c.name == column_name)
        except RuntimeError:
            self.fail(f'Column {column_name} not found in table {"table_child"}')

    def test_db_created(self):
        db: Database = self.create_db()
        db_file: pathlib.Path = pathlib.Path(db.filename)
        if not db_file.exists():
            self.fail("database was not created")

    def test_obj_created(self):
        db: Database = self.create_db()
        connection: sqlite3.Connection
        with db.create_connection() as connection:
            obj: ParentObject = db.query_object(connection, ParentObject, TABLE_PARENT, 1)
        self.assertTrue(obj is not None)

    def create_db(self) -> Database:
        db_json: Dict = utils.get_file_json('testfiles/db_definition.json')
        db: Database = Database.from_json(db_json)
        db.create_tables()
        parent_obj: ParentObject = ParentObject()
        parent_obj.id_table_parent = 1
        parent_obj.value_1 = 'test str parent'
        child_obj = ChildObject()
        child_obj.id_table_child = 100
        child_obj.value_1 = 'test str child'
        parent_obj.children.append(child_obj)
        db.save(parent_obj)
        return db


