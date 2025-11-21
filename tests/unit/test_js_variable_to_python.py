# -*- coding: utf-8 -*-
"""Tests for the function ``searx.utils.js_obj_str_to_python``

The tests are copied from:

https://github.com/Nykakin/chompjs/blob/c1501b5cd82c0044539875331745b820e7bfd067/chompjs/test_parser.py

The commented-out tests are not yet supported by the current implementation.
"""
# pylint: disable=missing-class-docstring, invalid-name

import math

from parameterized import parameterized

from searx.utils import js_obj_str_to_python

from tests import SearxTestCase


class TestParser(SearxTestCase):
    @parameterized.expand(
        [
            ("{'hello': 'world'}", {'hello': 'world'}),
            ("{'hello': 'world', 'my': 'master'}", {'hello': 'world', 'my': 'master'}),
            (
                "{'hello': 'world', 'my': {'master': 'of Orion'}, 'test': 'xx'}",
                {'hello': 'world', 'my': {'master': 'of Orion'}, 'test': 'xx'},
            ),
            ("{}", {}),
        ]
    )
    def test_parse_object(self, js, expected_py):
        py = js_obj_str_to_python(js)
        self.assertEqual(py, expected_py)

    @parameterized.expand(
        [
            ("[]", []),
            ("[[[]]]", [[[]]]),
            ("[[[1]]]", [[[1]]]),
            ("[1]", [1]),
            ("[1, 2, 3, 4]", [1, 2, 3, 4]),
            ("['h', 'e', 'l', 'l', 'o']", ['h', 'e', 'l', 'l', 'o']),
            ("[[[[[[[[[[[[[[[1]]]]]]]]]]]]]]]", [[[[[[[[[[[[[[[1]]]]]]]]]]]]]]]),
        ]
    )
    def test_parse_list(self, js, expected_py):
        py = js_obj_str_to_python(js)
        self.assertEqual(py, expected_py)

    @parameterized.expand(
        [
            ("{'hello': [], 'world': [0]}", {'hello': [], 'world': [0]}),
            ("{'hello': [1, 2, 3, 4]}", {'hello': [1, 2, 3, 4]}),
            ("[{'a':12}, {'b':33}]", [{'a': 12}, {'b': 33}]),
            (
                "[false, {'true': true, `pies`: \"kot\"}, false,]",
                [False, {"true": True, 'pies': 'kot'}, False],
            ),
            (
                "{a:1,b:1,c:1,d:1,e:1,f:1,g:1,h:1,i:1,j:1}",
                {k: 1 for k in 'abcdefghij'},
            ),
            (
                "{'a':[{'b':1},{'c':[{'d':{'f':{'g':[1,2]}}},{'e':1}]}]}",
                {'a': [{'b': 1}, {'c': [{'d': {'f': {'g': [1, 2]}}}, {'e': 1}]}]},
            ),
        ]
    )
    def test_parse_mixed(self, js, expected_py):
        py = js_obj_str_to_python(js)
        self.assertEqual(py, expected_py)

    @parameterized.expand(
        [
            ("{'hello': 12, 'world': 10002.21}", {'hello': 12, 'world': 10002.21}),
            ("[12, -323, 0.32, -32.22, .2, - 4]", [12, -323, 0.32, -32.22, 0.2, -4]),
            ('{"a": -12, "b": - 5}', {'a': -12, 'b': -5}),
            ("{'a': true, 'b': false, 'c': null}", {'a': True, 'b': False, 'c': None}),
            ("[\"\\uD834\\uDD1E\"]", ['𝄞']),
            ("{'a': '123\\'456\\n'}", {'a': "123'456\n"}),
            ("['\u00e9']", ['é']),
            ('{"cache":{"\u002ftest\u002f": 0}}', {'cache': {'/test/': 0}}),
            ('{"a": 3.125e7}', {'a': 3.125e7}),
            ('''{"a": "b\\'"}''', {'a': "b'"}),
            ('{"a": .99, "b": -.1}', {"a": 0.99, "b": -0.1}),
            ('["/* ... */", "// ..."]', ["/* ... */", "// ..."]),
            ('{"inclusions":["/*","/"]}', {'inclusions': ['/*', '/']}),
        ]
    )
    def test_parse_standard_values(self, js, expected_py):
        py = js_obj_str_to_python(js)
        self.assertEqual(py, expected_py)

    def test_parse_nan(self):
        js = '{"A": NaN}'
        py = js_obj_str_to_python(js)
        self.assertTrue(math.isnan(py["A"]))

    @parameterized.expand(
        [
            ("{abc: 100, dev: 200}", {'abc': 100, 'dev': 200}),
            ("{abcdefghijklmnopqrstuvwxyz: 12}", {"abcdefghijklmnopqrstuvwxyz": 12}),
            # (
            #     "{age: function(yearBorn,thisYear) {return thisYear - yearBorn;}}",
            #     {"age": "function(yearBorn,thisYear) {return thisYear - yearBorn;}"}
            # ),
            # (
            #     "{\"abc\": function() {return '])))))))))))))))';}}",
            #     {"abc": "function() {return '])))))))))))))))';}"},
            # ),
            ('{"a": undefined}', {"a": None}),  # chompjs returns {"a": "undefined"}
            ('[undefined, undefined]', [None, None]),  # chompjs returns ["undefined", "undefined"]
            ("{_a: 1, $b: 2}", {"_a": 1, "$b": 2}),
            # ("{regex: /a[^d]{1,12}/i}", {'regex': '/a[^d]{1,12}/i'}),
            # ("{'a': function(){return '\"'}}", {'a': 'function(){return \'"\'}'}),
            ("{1: 1, 2: 2, 3: 3, 4: 4}", {'1': 1, '2': 2, '3': 3, '4': 4}),
            ("{'a': 121.}", {'a': 121.0}),
        ]
    )
    def test_parse_strange_values(self, js, expected_py):
        py = js_obj_str_to_python(js)
        self.assertEqual(py, expected_py)

    @parameterized.expand(
        [
            # ('{"a": {"b": [12, 13, 14]}}text text', {"a": {"b": [12, 13, 14]}}),
            # ('var test = {"a": {"b": [12, 13, 14]}}', {"a": {"b": [12, 13, 14]}}),
            ('{"a":\r\n10}', {'a': 10}),
            ("{'foo': 0,\r\n}", {'foo': 0}),
            ("{truefalse: 0, falsefalse: 1, nullnull: 2}", {'truefalse': 0, 'falsefalse': 1, 'nullnull': 2}),
        ]
    )
    def test_strange_input(self, js, expected_py):
        py = js_obj_str_to_python(js)
        self.assertEqual(py, expected_py)

    @parameterized.expand(
        [
            ("[0]", [0]),
            ("[1]", [1]),
            ("[12]", [12]),
            ("[12_12]", [1212]),
            # ("[0x12]", [18]),
            # ("[0xab]", [171]),
            # ("[0xAB]", [171]),
            # ("[0X12]", [18]),
            # ("[0Xab]", [171]),
            # ("[0XAB]", [171]),
            # ("[01234]", [668]),
            # ("[0o1234]", [668]),
            # ("[0O1234]", [668]),
            # ("[0b1111]", [15]),
            # ("[0B1111]", [15]),
            ("[-0]", [-0]),
            ("[-1]", [-1]),
            ("[-12]", [-12]),
            ("[-12_12]", [-1212]),
            # ("[-0x12]", [-18]),
            # ("[-0xab]", [-171]),
            # ("[-0xAB]", [-171]),
            # ("[-0X12]", [-18]),
            # ("[-0Xab]", [-171]),
            # ("[-0XAB]", [-171]),
            # ("[-01234]", [-668]),
            # ("[-0o1234]", [-668]),
            # ("[-0O1234]", [-668]),
            # ("[-0b1111]", [-15]),
            # ("[-0B1111]", [-15]),
        ]
    )
    def test_integer_numeric_values(self, js, expected_py):
        py = js_obj_str_to_python(js)
        self.assertEqual(py, expected_py)

    @parameterized.expand(
        [
            ("[0.32]", [0.32]),
            ("[-0.32]", [-0.32]),
            ("[.32]", [0.32]),
            ("[-.32]", [-0.32]),
            ("[12.]", [12.0]),
            ("[-12.]", [-12.0]),
            ("[12.32]", [12.32]),
            ("[-12.12]", [-12.12]),
            ("[3.1415926]", [3.1415926]),
            ("[.123456789]", [0.123456789]),
            ("[.0123]", [0.0123]),
            ("[0.0123]", [0.0123]),
            ("[-.0123]", [-0.0123]),
            ("[-0.0123]", [-0.0123]),
            ("[3.1E+12]", [3.1e12]),
            ("[3.1e+12]", [3.1e12]),
            ("[.1e-23]", [0.1e-23]),
            ("[.1e-23]", [0.1e-23]),
        ]
    )
    def test_float_numeric_values(self, js, expected_py):
        py = js_obj_str_to_python(js)
        self.assertEqual(py, expected_py)

    # @parameterized.expand([
    #     ('["Test\\nDrive"]\n{"Test": "Drive"}', [['Test\nDrive'], {'Test': 'Drive'}]),
    # ])
    # def test_jsonlines(self, js, expected_py):
    #     py = js_obj_str_to_python(js)
    #     self.assertEqual(py, expected_py)


class TestParserExceptions(SearxTestCase):
    @parameterized.expand(
        [
            ('}{', ValueError),
            ('', ValueError),
            (None, ValueError),
        ]
    )
    def test_exceptions(self, js, expected_exception):
        with self.assertRaises(expected_exception):
            js_obj_str_to_python(js)

    @parameterized.expand(
        [
            ("{whose: 's's', category_name: '>'}", ValueError),
        ]
    )
    def test_malformed_input(self, in_data, expected_exception):
        with self.assertRaises(expected_exception):
            js_obj_str_to_python(in_data)

    @parameterized.expand(
        [
            (
                '{"test": """}',
                ValueError,
                'js_obj_str_to_python creates invalid JSON',
            ),
        ]
    )
    def test_error_messages(self, js, expected_exception, expected_exception_text):
        with self.assertRaisesRegex(expected_exception, expected_exception_text):
            js_obj_str_to_python(js)


# class TestOptions(SearxTestCase):
#     @parameterized.expand(
#         [
#             ('{\\\"a\\\": 12}', {'a': 12}),
#         ]
#     )
#     def test_unicode_escape(self, js, expected_py):
#         py = js_obj_str_to_python(js)
#         self.assertEqual(py, expected_py)


class TestParseJsonObjects(SearxTestCase):
    @parameterized.expand(
        [
            # ("", []),
            # ("aaaaaaaaaaaaaaaa", []),
            # ("         ", []),
            ("      {'a': 12}", [{'a': 12}]),
            # ("[1, 2, 3, 4]xxxxxxxxxxxxxxxxxxxxxxxx", [[1, 2, 3, 4]]),
            # ("[12] [13] [14]", [[12], [13], [14]]),
            # ("[10] {'a': [1, 1, 1,]}", [[10], {'a': [1, 1, 1]}]),
            # ("[1][1][1]", [[1], [1], [1]]),
            # ("[1] [2] {'a': ", [[1], [2]]),
            # ("[]", [[]]),
            # ("[][][][]", [[], [], [], []]),
            ("{}", [{}]),
            # ("{}{}{}{}", [{}, {}, {}, {}]),
            # ("{{}}{{}}", []),
            # ("[[]][[]]", [[[]], [[]]]),
            # ("{am: 'ab'}\n{'ab': 'xx'}", [{'am': 'ab'}, {'ab': 'xx'}]),
            # (
            #     'function(a, b, c){ /* ... */ }({"a": 12}, Null, [1, 2, 3])',
            #     [{}, {'a': 12}, [1, 2, 3]],
            # ),
            # ('{"a": 12, broken}{"c": 100}', [{'c': 100}]),
            # ('[12,,,,21][211,,,][12,12][12,,,21]', [[12, 12]]),
        ]
    )
    def test_parse_json_objects(self, js, expected_py):
        py_in_list = [js_obj_str_to_python(js)]
        self.assertEqual(py_in_list, expected_py)
