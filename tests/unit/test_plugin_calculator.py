# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

import flask
from parameterized.parameterized import parameterized
from searx import plugins
from searx import preferences
from tests import SearxTestCase
from .test_utils import random_string

from .test_plugins import get_search_mock


class PluginCalculator(SearxTestCase):  # pylint: disable=missing-class-docstring

    def setUp(self):
        from searx import webapp  # pylint: disable=import-outside-toplevel

        self.webapp = webapp
        self.store = plugins.PluginStore()
        plugin = plugins.load_and_initialize_plugin('searx.plugins.calculator', False, (None, {}))
        self.store.register(plugin)
        self.preferences = preferences.Preferences(["simple"], ["general"], {}, self.store)
        self.preferences.parse_dict({"locale": "en"})

    def test_plugin_store_init(self):
        self.assertEqual(1, len(self.store.plugins))

    def test_single_page_number_true(self):
        with self.webapp.app.test_request_context():
            flask.request.preferences = self.preferences
            search = get_search_mock(query=random_string(10), pageno=2)
            result = self.store.call(self.store.plugins, 'post_search', flask.request, search)

        self.assertTrue(result)
        self.assertNotIn('calculate', search.result_container.answers)

    def test_long_query_true(self):
        with self.webapp.app.test_request_context():
            flask.request.preferences = self.preferences
            search = get_search_mock(query=random_string(101), pageno=1)
            result = self.store.call(self.store.plugins, 'post_search', flask.request, search)

        self.assertTrue(result)
        self.assertNotIn('calculate', search.result_container.answers)

    def test_alpha_true(self):
        with self.webapp.app.test_request_context():
            flask.request.preferences = self.preferences
            search = get_search_mock(query=random_string(10), pageno=1)
            result = self.store.call(self.store.plugins, 'post_search', flask.request, search)

        self.assertTrue(result)
        self.assertNotIn('calculate', search.result_container.answers)

    @parameterized.expand(
        [
            ("1+1", "2", "en"),
            ("1-1", "0", "en"),
            ("1*1", "1", "en"),
            ("1/1", "1", "en"),
            ("1**1", "1", "en"),
            ("1^1", "1", "en"),
            ("1,000.0+1,000.0", "2,000", "en"),
            ("1.0+1.0", "2", "en"),
            ("1.0-1.0", "0", "en"),
            ("1.0*1.0", "1", "en"),
            ("1.0/1.0", "1", "en"),
            ("1.0**1.0", "1", "en"),
            ("1.0^1.0", "1", "en"),
            ("1.000,0+1.000,0", "2.000", "de"),
            ("1,0+1,0", "2", "de"),
            ("1,0-1,0", "0", "de"),
            ("1,0*1,0", "1", "de"),
            ("1,0/1,0", "1", "de"),
            ("1,0**1,0", "1", "de"),
            ("1,0^1,0", "1", "de"),
        ]
    )
    def test_localized_query(self, operation: str, contains_result: str, lang: str):
        with self.webapp.app.test_request_context():
            self.preferences.parse_dict({"locale": lang})
            flask.request.preferences = self.preferences
            search = get_search_mock(query=operation, lang=lang, pageno=1)
            result = self.store.call(self.store.plugins, 'post_search', flask.request, search)

        self.assertTrue(result)
        self.assertIn('calculate', search.result_container.answers)
        self.assertIn(contains_result, search.result_container.answers['calculate']['answer'])

    @parameterized.expand(
        [
            "1/0",
        ]
    )
    def test_invalid_operations(self, operation):
        with self.webapp.app.test_request_context():
            flask.request.preferences = self.preferences
            search = get_search_mock(query=operation, pageno=1)
            result = self.store.call(self.store.plugins, 'post_search', flask.request, search)

        self.assertTrue(result)
        self.assertNotIn('calculate', search.result_container.answers)
