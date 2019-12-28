import unittest
from typing import List

from wordparser import ParserGroup, ParserType, WordParser, GroupQuantityType


class TestParserGroup(unittest.TestCase):
    def test_from_str(self):
        g = ParserGroup.from_str('name:w')
        self.assertEqual(g.name, 'name')
        self.assertEqual(g.type, ParserType.WORD)
        self.assertEqual(g.quantity_type, GroupQuantityType.SINGLE)
        self.assertEqual(g.quantity, 1)

        g = ParserGroup.from_str('name:2w')
        self.assertEqual(g.name, 'name')
        self.assertEqual(g.type, ParserType.WORD)
        self.assertEqual(g.quantity_type, GroupQuantityType.LIST)
        self.assertEqual(g.quantity, 2)

        g = ParserGroup.from_str('name:*w')
        self.assertEqual(g.name, 'name')
        self.assertEqual(g.type, ParserType.WORD)
        self.assertEqual(g.quantity_type, GroupQuantityType.ANY)

        g = ParserGroup.from_str('interval:*t')
        self.assertEqual(g.name, 'interval')
        self.assertEqual(g.type, ParserType.TIME_INTERVAL)
        self.assertEqual(g.quantity_type, GroupQuantityType.ANY)

    def test_eq(self):
        g1 = ParserGroup.from_str('p1:w')
        g2 = ParserGroup.from_str('p1:w')
        g3 = ParserGroup.from_str('p2:w')
        g4 = ParserGroup.from_str('p2:n')
        self.assertTrue(g1 == g2)
        self.assertTrue(g1 != g3)
        self.assertTrue(g1 != g4)
        self.assertFalse(g1 != g2)
        self.assertFalse(g1 == g3)
        self.assertFalse(g1 == g4)


class TestWordParser(unittest.TestCase):
    def test_from_str(self):
        wp = WordParser.from_str('p1:w p2:2n p3:*w')
        self.assertEqual(len(wp.groups), 3)
        self.assertEqual(wp.groups[0], ParserGroup.from_str('p1:w'))
        self.assertEqual(wp.groups[1], ParserGroup.from_str('p2:2n'))
        self.assertEqual(wp.groups[2], ParserGroup.from_str('p3:*w'))

    def test_match_1_w(self):
        wp = WordParser.from_str('p1:w')
        res = wp.match('hello')
        self.assertTrue(res.success)
        self.assertEqual(res.results['p1'], 'hello')

    def test_match_2_w(self):
        wp = WordParser.from_str('p1:w p2:w')
        res = wp.match('hello world')
        self.assertTrue(res.success)
        self.assertEqual(res.results['p1'], 'hello')
        self.assertEqual(res.results['p2'], 'world')

    def test_match_2w(self):
        wp = WordParser.from_str('p1:2w')
        res = wp.match('hello world')
        self.assertTrue(res.success)
        self.assertEqual(len(res.results['p1']), 2)
        self.assertEqual(res.results['p1'][0], 'hello')
        self.assertEqual(res.results['p1'][1], 'world')

    def test_match_2w_error(self):
        wp = WordParser.from_str('p1:2w')
        res = wp.match('hello')
        self.assertFalse(res.success)

    def test_match_1_n(self):
        wp = WordParser.from_str('p1:n')
        res = wp.match('1234')
        self.assertTrue(res.success)
        self.assertEqual(res.results['p1'], 1234)

    def test_match_1_n_error(self):
        wp = WordParser.from_str('p1:n')
        res = wp.match('not_a_number')
        self.assertFalse(res.success)

    def test_match_1_w_any_n(self):
        wp = WordParser.from_str('word:w numbers:*n')
        res = wp.match('hello 1 2 3')
        self.assertTrue(res.success)
        self.assertEqual(res.results['word'], 'hello')
        self.assertTrue(len(res.results['numbers']) == 3)
        self.assertEqual(res.results['numbers'][0], 1)
        self.assertEqual(res.results['numbers'][1], 2)
        self.assertEqual(res.results['numbers'][2], 3)

    def test_match_time_interval(self):
        wp = WordParser.from_str('cmd:w duration:t msg:*w')
        res = wp.match('hello 1h30m a b c')
        self.assertTrue(res.success)
        self.assertEqual(res.results['cmd'], 'hello')
        self.assertAlmostEqual(res.results['duration'], 5400.)
        self.assertTrue(len(res.results['msg']) == 3)
        self.assertEqual(res.results['msg'][0], 'a')
        self.assertEqual(res.results['msg'][1], 'b')
        self.assertEqual(res.results['msg'][2], 'c')

    def test_parse_time_interval(self):
        data = ['1s', '5s', '1m30s', '1h20m5s', '1d8h30m10s']  # type: List[str]
        expected = [1., 5., 90., 4805., 117010.]  # type: List[float]

        for d, e in zip(data, expected):
            self.assertAlmostEqual(WordParser.parse_time_interval(d), e)


if __name__ == '__main__':
    unittest.main()
