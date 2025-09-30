# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

import warnings

from parameterized.parameterized import parameterized

import zhensa.plugins
import zhensa.preferences

from zhensa.extended_types import sxng_request
from zhensa.result_types import Answer

from tests import SearxTestCase
from .test_utils import random_string
from .test_plugins import do_post_search


# Reporting the DeprecationWarning once should be sufficient when running tests
warnings.filterwarnings("once", category=DeprecationWarning)


class PluginCalculator(SearxTestCase):

    def setUp(self):
        super().setUp()
        engines = {}

        self.storage = zhensa.plugins.PluginStorage()
        self.storage.load_settings({"zhensa.plugins.calculator.SXNGPlugin": {"active": True}})
        self.storage.init(self.app)
        self.pref = zhensa.preferences.Preferences(["simple"], ["general"], engines, self.storage)
        self.pref.parse_dict({"locale": "en"})

    def test_plugin_store_init(self):
        self.assertEqual(1, len(self.storage))

    def test_pageno_1_2(self):
        with self.app.test_request_context():
            sxng_request.preferences = self.pref
            query = "1+1"
            answer = Answer(answer=f"{query} = {eval(query)}")  # pylint: disable=eval-used

            search = do_post_search(query, self.storage, pageno=1)
            self.assertIn(answer, search.result_container.answers)

            search = do_post_search(query, self.storage, pageno=2)
            self.assertEqual(list(search.result_container.answers), [])

    def test_long_query_ignored(self):
        with self.app.test_request_context():
            sxng_request.preferences = self.pref
            query = f"1+1 {random_string(101)}"
            search = do_post_search(query, self.storage)
            self.assertEqual(list(search.result_container.answers), [])

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
    def test_localized_query(self, query: str, res: str, lang: str):
        with self.app.test_request_context():
            self.pref.parse_dict({"locale": lang})
            sxng_request.preferences = self.pref
            answer = Answer(answer=f"{query} = {res}")

            search = do_post_search(query, self.storage)
            self.assertIn(answer, search.result_container.answers)

    @parameterized.expand(
        [
            "1/0",
        ]
    )
    def test_invalid_operations(self, query):
        with self.app.test_request_context():
            sxng_request.preferences = self.pref
            search = do_post_search(query, self.storage)
            self.assertEqual(list(search.result_container.answers), [])
