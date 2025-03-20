# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

from parameterized.parameterized import parameterized

from flask_babel import gettext

import searx.plugins
import searx.preferences
import searx.limiter
import searx.botdetection

from searx.extended_types import sxng_request
from searx.result_types import Answer

from tests import SearxTestCase
from .test_plugins import do_post_search


class PluginIPSelfInfo(SearxTestCase):

    def setUp(self):
        super().setUp()
        engines = {}

        self.storage = searx.plugins.PluginStorage()
        self.storage.load_settings({"searx.plugins.self_info.SXNGPlugin": {"active": True}})
        self.storage.init(self.app)
        self.pref = searx.preferences.Preferences(["simple"], ["general"], engines, self.storage)
        self.pref.parse_dict({"locale": "en"})

        cfg = searx.limiter.get_cfg()
        searx.botdetection.init(cfg, None)

    def test_plugin_store_init(self):
        self.assertEqual(1, len(self.storage))

    def test_pageno_1_2(self):

        with self.app.test_request_context():
            sxng_request.preferences = self.pref
            sxng_request.remote_addr = "127.0.0.1"
            sxng_request.headers = {"X-Forwarded-For": "1.2.3.4, 127.0.0.1", "X-Real-IP": "127.0.0.1"}  # type: ignore
            answer = Answer(answer=gettext("Your IP is: ") + "127.0.0.1")

            search = do_post_search("ip", self.storage, pageno=1)
            self.assertIn(answer, search.result_container.answers)

            search = do_post_search("ip", self.storage, pageno=2)
            self.assertEqual(list(search.result_container.answers), [])

    @parameterized.expand(
        [
            "user-agent",
            "USER-AgenT lorem ipsum",
        ]
    )
    def test_user_agent_in_answer(self, query: str):

        query = "user-agent"

        with self.app.test_request_context():
            sxng_request.preferences = self.pref
            sxng_request.user_agent = "Dummy agent"  # type: ignore
            answer = Answer(answer=gettext("Your user-agent is: ") + "Dummy agent")

            search = do_post_search(query, self.storage, pageno=1)
            self.assertIn(answer, search.result_container.answers)

            search = do_post_search(query, self.storage, pageno=2)
            self.assertEqual(list(search.result_container.answers), [])
