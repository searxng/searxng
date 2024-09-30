# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

from unittest.mock import MagicMock, Mock
from searx.engines import load_engines, mariadb_server
from tests import SearxTestCase


class MariadbServerTests(SearxTestCase):  # pylint: disable=missing-class-docstring
    def setUp(self):
        load_engines(
            [
                {
                    'name': 'mariadb server',
                    'engine': 'mariadb_server',
                    'shortcut': 'mdb',
                    'timeout': 9.0,
                    'disabled': True,
                }
            ]
        )

    def tearDown(self):
        load_engines([])

    def test_init_no_query_str_raises(self):
        self.assertRaises(ValueError, lambda: mariadb_server.init({}))

    def test_init_non_select_raises(self):
        self.assertRaises(ValueError, lambda: mariadb_server.init({'query_str': 'foobar'}))

    def test_search_returns_results(self):
        test_string = 'FOOBAR'
        cursor_mock = MagicMock()
        with cursor_mock as setup:  # pylint: disable=not-context-manager
            setup.__iter__ = Mock(return_value=iter([{test_string, 1}]))
            setup.description = [[test_string]]
        conn_mock = Mock()
        conn_mock.cursor.return_value = cursor_mock
        mariadb_server._connection = conn_mock  # pylint: disable=protected-access
        results = mariadb_server.search(test_string, {'pageno': 1})
        self.assertEqual(1, len(results))
        self.assertIn(test_string, results[0])
        self.assertEqual(mariadb_server.result_template, results[0]['template'])
