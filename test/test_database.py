import unittest

import pathlib
from typing import Dict
from typing import List

import sqlite3

import utils
from db.database import DataTable
from db.database import Database, DbSerializable, DataSet, DataRow

TABLE_PARENT = 'table_parent'
TABLE_CHILD = 'table_child'


class ChildObject(DbSerializable):
    def __init__(self):
        self.id_table_child = 0  # type: int
        self.value_1 = ''  # type: str

    @classmethod
    def from_data_set(cls, data_set: DataSet) -> List['DbSerializable']:
        pass

    def to_data_set(self) -> DataSet:
        ds = DataSet()
        row = DataRow(TABLE_CHILD, self.id_table_child)
        row.put('id_table_child', self.id_table_child)
        row.put('value_1', self.value_1)
        ds.merge_row(row)
        return ds


class ParentObject(DbSerializable):
    def __init__(self):
        self.id_table_parent = 0  # type: int
        self.value_1 = ''  # type: str
        self.children = []  # type: List[ChildObject]

    def to_data_set(self) -> DataSet:
        ds = DataSet()
        row = DataRow(TABLE_PARENT , self.id_table_parent)
        row.put('id_table_parent', self.id_table_parent)
        row.put('value_1', self.value_1)
        ds.merge_row(row)
        for child in self.children:
            child_ds = child.to_data_set()  # type: Dataset
            child_ds.add_column_to_table(TABLE_CHILD, 'id_table_parent', self.id_table_parent)
            ds.merge(child_ds)
        return ds

    @classmethod
    def from_data_set(cls, data_set: DataSet) -> List['ParentObject']:
        res = []  # type: List[ParentObject]
        table = data_set.tables[TABLE_PARENT]
        for row_key in table.rows:  # type: DataRow
            obj = ParentObject()
            obj.id_table_parent = table.rows[row_key].get('id_table_parent')
            obj.value_1 = table.rows[row_key].get('value_1')
            res.append(obj)
        return res


class TestDatabase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        db_file = pathlib.Path('test.sqlite')
        if db_file.exists():
            db_file.unlink()

    def test_from_json(self):
        db_json = utils.get_file_json('testfiles/db_definition.json')
        db = Database.from_json(db_json)
        self.assertEqual(len(db.tables), 2)
        try:
            parent_table = db.get_table(TABLE_PARENT)
            child_table = db.get_table('table_child')
        except RuntimeError:
            self.fail("get_table() raised RuntimeError unexpectedly!")
        columns = ['id_table_parent', 'value_1']
        try:
            for column_name in columns:
                col = utils.first_where(parent_table.columns, lambda c: c.name == column_name)
        except RuntimeError:
            self.fail('Column {0} not found in table {1}'.format(column_name, TABLE_PARENT))
        columns = ['id_table_child', 'id_table_parent', 'value_1']
        try:
            for column_name in columns:
                col = utils.first_where(child_table.columns, lambda c: c.name == column_name)
        except RuntimeError:
            self.fail('Column {0} not found in table {1}'.format(column_name, 'table_child'))

    def test_db_created(self):
        db = self.create_db()  # type: Database
        db_file = pathlib.Path(db.filename)  # type: pathlib.Path
        if not db_file.exists():
            self.fail("database was not created")

    def test_obj_created(self):
        db = self.create_db()  # type: Database
        with db.create_connection() as connection:  # type: sqlite3.Connection
            obj = db.query_object(connection, ParentObject, TABLE_PARENT, 1)  # type: ParentObject
        self.assertTrue(obj is not None)

    def create_db(self) -> Database:
        db_json = utils.get_file_json('testfiles/db_definition.json')  # type: Dict
        db = Database.from_json(db_json)  # type: Database
        db.create_tables()
        parent_obj = ParentObject()  # type: ParentObject
        parent_obj.id_table_parent = 1
        parent_obj.value_1 = 'test str parent'
        child_obj = ChildObject()
        child_obj.id_table_child = 100
        child_obj.value_1 = 'test str child'
        parent_obj.children.append(child_obj)
        db.save(parent_obj)
        return db


