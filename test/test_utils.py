import unittest

import utils


class TestUtils(unittest.TestCase):
    def test_indexof_success(self):
        l = [0, 1, 2, 3, 0]
        self.assertEqual(len(utils.index_of(l, 0)), 2)
        self.assertTrue(0 in utils.index_of(l, 0))
        self.assertTrue(4 in utils.index_of(l, 0))
        self.assertEqual(len(utils.index_of(l, 1)), 1)
        self.assertTrue(1 in utils.index_of(l, 1))
        self.assertEqual(len(utils.index_of(l, 2)), 1)
        self.assertTrue(2 in utils.index_of(l, 2))
        self.assertEqual(len(utils.index_of(l, 3)), 1)
        self.assertTrue(3 in utils.index_of(l, 3))

    def test_indexof_notsuccess(self):
        l = [0, 1, 2, 3, 0]
        self.assertEqual(len(utils.index_of(l, 4)), 0)
