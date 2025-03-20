# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

from parameterized.parameterized import parameterized

import searx.plugins
import searx.preferences

from searx.extended_types import sxng_request
from searx.result_types import Answer

from tests import SearxTestCase
from .test_plugins import do_post_search

query_res = [
    ("md5 test", "md5 hash digest: 098f6bcd4621d373cade4e832627b4f6"),
    ("sha1 test", "sha1 hash digest: a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"),
    ("sha224 test", "sha224 hash digest: 90a3ed9e32b2aaf4c61c410eb925426119e1a9dc53d4286ade99a809"),
    ("sha256 test", "sha256 hash digest: 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"),
    (
        "sha384 test",
        "sha384 hash digest: 768412320f7b0aa5812fce428dc4706b3c"
        "ae50e02a64caa16a782249bfe8efc4b7ef1ccb126255d196047dfedf1"
        "7a0a9",
    ),
    (
        "sha512 test",
        "sha512 hash digest: ee26b0dd4af7e749aa1a8ee3c10ae9923f6"
        "18980772e473f8819a5d4940e0db27ac185f8a0e1d5f84f88bc887fd67b143732c304cc5"
        "fa9ad8e6f57f50028a8ff",
    ),
]


class PluginHashTest(SearxTestCase):

    def setUp(self):
        super().setUp()
        engines = {}

        self.storage = searx.plugins.PluginStorage()
        self.storage.load_settings({"searx.plugins.hash_plugin.SXNGPlugin": {"active": True}})
        self.storage.init(self.app)
        self.pref = searx.preferences.Preferences(["simple"], ["general"], engines, self.storage)
        self.pref.parse_dict({"locale": "en"})

    def test_plugin_store_init(self):
        self.assertEqual(1, len(self.storage))

    @parameterized.expand(query_res)
    def test_hash_digest_new(self, query: str, res: str):
        with self.app.test_request_context():
            sxng_request.preferences = self.pref
            answer = Answer(answer=res)

            search = do_post_search(query, self.storage)
            self.assertIn(answer, search.result_container.answers)

    def test_pageno_1_2(self):
        with self.app.test_request_context():
            sxng_request.preferences = self.pref
            query, res = query_res[0]
            answer = Answer(answer=res)

            search = do_post_search(query, self.storage, pageno=1)
            self.assertIn(answer, search.result_container.answers)

            search = do_post_search(query, self.storage, pageno=2)
            self.assertEqual(list(search.result_container.answers), [])
