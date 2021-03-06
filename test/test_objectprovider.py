import unittest

import pathlib
from sqlite3.dbapi2 import Connection
from typing import List

from db.database import Database, DataSet
from objectprovider import ObjectProvider
from test.dbdata import ParentObject, ChildObject


class TestObjectProvider(unittest.TestCase):
    def setUp(self):
        self.database = Database.load_from_json_file('testfiles/db_definition.json')
        self.database.create_tables()
        p1: ParentObject = ParentObject()
        p1.id_table_parent = 1
        c1: ChildObject = ChildObject()
        c1.id_table_child = 1
        c1.value_1 = 'c1'
        p1.single_child = c1
        c2: ChildObject = ChildObject()
        c2.id_table_child = 2
        c2.value_1 = 'c2'
        p1.children.append(c2)
        c3: ChildObject = ChildObject()
        c3.id_table_child = 3
        c3.value_1 = 'c3'
        p1.children.append(c3)
        self.database.save(p1)

    def tearDown(self):
        db_file: pathlib.Path = pathlib.Path('test.sqlite')
        if db_file.exists():
            db_file.unlink()

    def test_from_json(self):
        object_provider: ObjectProvider = ObjectProvider.load_from_json_file('testfiles/op_definition.json')

    def test_save_object(self):
        p: ParentObject = ParentObject()
        p.id_table_parent = 2
        p.children = []
        object_provider: ObjectProvider = ObjectProvider.load_from_json_file('testfiles/op_definition.json')
        connection: Connection
        with self.database.create_connection() as connection:
            ds: DataSet = object_provider._object_to_dataset(self.database, connection, p)
            self.database.save_data_set(connection, ds)
        with self.database.create_connection() as connection:
            self.database.raw_query(connection, 'table_parent', ['id_table_parent', 'value_1'], None, None)
            res: List[object] = object_provider._query_objects(self.database, connection, 'test.dbdata.ParentObject', None, None)
            print(res)
