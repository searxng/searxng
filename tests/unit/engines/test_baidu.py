# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring
"""Test the Baidu engine's error handling.

Baidu answers with a CAPTCHA in two different ways, both of which must suspend
the engine for a short time instead of leaking an unrelated exception:

1. HTTP 302 redirect to ``wappass.baidu.com/static/captcha``
2. HTTP 200 with an HTML page instead of the expected JSON payload
"""

from unittest.mock import Mock

from searx.engines import baidu
from searx.exceptions import SearxEngineAPIException, SearxEngineCaptchaException

from tests import SearxTestCase


class BaiduResponseTests(SearxTestCase):  # pylint: disable=missing-class-docstring
    def setUp(self):
        super().setUp()
        baidu.baidu_category = "general"

    def test_captcha_redirect(self):
        response = Mock()
        response.headers = {"Location": "https://wappass.baidu.com/static/captcha/tuxing_v2.html?ak=x"}
        response.text = ""
        with self.assertRaises(SearxEngineCaptchaException) as ctx:
            baidu.response(response)
        self.assertEqual(baidu.CAPTCHA_SUSPEND_TIME, ctx.exception.suspended_time)

    def test_html_body(self):
        # HTTP 200 with an HTML soft-block page: no CAPTCHA redirect, but the
        # body is not JSON either.
        response = Mock()
        response.headers = {}
        response.text = "<!DOCTYPE html><html><head><title>网络不给力</title></head><body></body></html>"
        with self.assertRaises(SearxEngineCaptchaException) as ctx:
            baidu.response(response)
        self.assertEqual(baidu.CAPTCHA_SUSPEND_TIME, ctx.exception.suspended_time)

    def test_suspend_time_shorter(self):
        # The default (search.suspended_times.SearxEngineCaptcha) is 86400 sec,
        # but Baidu lifts a block within seconds/minutes: a too long suspension
        # disables the engine long after Baidu is reachable again.
        self.assertLess(baidu.CAPTCHA_SUSPEND_TIME, 3600)

    def test_empty_json(self):
        # An empty JSON object is not treated as a CAPTCHA: the engine reports
        # it as an invalid response (pre-existing behavior).
        response = Mock()
        response.headers = {}
        response.text = "{}"
        self.assertRaises(SearxEngineAPIException, lambda: baidu.response(response))
