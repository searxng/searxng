# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name,line-too-long

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

    def test_IPv4_X_Forwarded_For(self):
        headers = {"X-Forwarded-For": "1.2.3.4, 127.0.0.1"}
        answer = gettext("Your IP is: ") + "1.2.3.4"

        result = self.client.post("/search", data={"q": "ip"}, headers=headers)
        self.assertIn(answer, str(result.data))
        result = self.client.post("/search", data={"q": "ip", "pageno": "2"}, headers=headers)
        self.assertNotIn(answer, str(result.data))

    def test_IPv6_X_Forwarded_For(self):
        headers = {
            "X-Forwarded-For": "fd0f:a306:f289:0000:0000:0000:ffff:bbbb, ::1, 127.0.0.1",
            "X-Real-IP": "fd0f:a306:f289:0000:0000:0000:ffff:aaaa",
        }
        # value from X-Forwarded-For should win
        answer = gettext("Your IP is: ") + "fd0f:a306:f289::ffff:bbbb"
        result = self.client.post("/search", data={"q": "ip"}, headers=headers)
        self.assertIn(answer, str(result.data))

    def test_IPv6_X_Forwarded_For_all_trusted(self):
        headers = {
            "X-Forwarded-For": "127.0.0.1, 127.0.0.2, 127.0.0.3, ::1",
        }
        # value from X-Forwarded-For should win
        answer = gettext("Your IP is: ") + "127.0.0.1"
        result = self.client.post("/search", data={"q": "ip"}, headers=headers)
        self.assertIn(answer, str(result.data))

    def test_IPv6_X_Real_IP(self):
        headers = {
            "X-Real-IP": "fd0f:a306:f289:0000:0000:0000:ffff:aaaa",
        }
        # X-Forwarded-For is not set, X-Real-IP should win
        answer = gettext("Your IP is: ") + "fd0f:a306:f289::ffff:aaaa"
        result = self.client.post("/search", data={"q": "ip"}, headers=headers)
        self.assertIn(answer, str(result.data))

    def test_REMOTE_ADDR_is_invalid(self):
        # X-Forwarded-For and X-Real-IP ar unset and REMOTE_ADDR is invalid
        answer = gettext("Your IP is: ") + "100::"
        headers = {}
        environ_overrides = {"REMOTE_ADDR": "1.2.3.4.5"}
        with self.assertLogs("searx.botdetection", level="ERROR") as ctx:
            result = self.client.post("/search", data={"q": "ip"}, headers=headers, environ_overrides=environ_overrides)
            self.assertIn(answer, str(result.data))
        self.assertIn(
            "ERROR:searx.botdetection:REMOTE_ADDR: '1.2.3.4.5' does not appear to be an IPv4 or IPv6 address / discard REMOTE_ADDR from WSGI environment",
            ctx.output,
        )

    def test_X_Real_IP_is_invalid(self):
        # when a client fakes a X-Real-IP header with an invalid IP 1.2.3.4.5 in
        answer = gettext("Your IP is: ") + "96.7.128.186"
        headers = {"X-Real-IP": "1.2.3.4.5", "X-Forwarded-For": "96.7.128.186, 127.0.0.1"}
        environ_overrides = {"REMOTE_ADDR": "127.0.0.1"}

        with self.assertLogs("searx.botdetection", level="ERROR") as ctx:
            result = self.client.post("/search", data={"q": "ip"}, headers=headers, environ_overrides=environ_overrides)
            self.assertIn(answer, str(result.data))
        self.assertIn(
            "ERROR:searx.botdetection:X-Real-IP: '1.2.3.4.5' does not appear to be an IPv4 or IPv6 address / discard HTTP_X_REAL_IP from WSGI environment",
            ctx.output,
        )

    def test_X_Forwarded_For_is_invalid(self):
        # when a client fakes a X-Forwarded-For header with an invalid IP
        # 1.2.3.4.5 in and the Proxy set a X-Real-IP
        answer = gettext("Your IP is: ") + "96.7.128.186"
        headers = {
            "X-Forwarded-For": "1.2.3.4, 1.2.3.4.5, 127.0.0.1",
            "X-Real-IP": "96.7.128.186",
        }
        with self.assertLogs("searx.botdetection", level="ERROR") as ctx:
            result = self.client.post("/search", data={"q": "ip"}, headers=headers)
            self.assertIn(answer, str(result.data))
        self.assertIn(
            "ERROR:searx.botdetection:X-Forwarded-For: '1.2.3.4.5' does not appear to be an IPv4 or IPv6 address / discard HTTP_X_FORWARDED_FOR from WSGI environment",
            ctx.output,
        )

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
