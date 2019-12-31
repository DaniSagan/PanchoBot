import unittest

import utils
from db.database import Database


class TestDatabase(unittest.TestCase):
    def test_from_json(self):
        db_json = utils.get_file_json('testfiles/db_definition.json')
        db = Database.from_json(db_json)
        self.assertEqual(len(db.tables), 2)
        try:
            parent_table = db.get_table('table_parent')
            child_table = db.get_table('table_child')
        except RuntimeError:
            self.fail("get_table() raised RuntimeError unexpectedly!")
