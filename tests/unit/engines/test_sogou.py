# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name

from unittest.mock import MagicMock

from lxml import html

from searx.engines import sogou
from searx.exceptions import SearxEngineCaptchaException
from tests import SearxTestCase


class TestSogou(SearxTestCase):

    def test_antispider_redirect_raises_captcha(self):
        resp = MagicMock()
        resp.status_code = 302
        resp.headers = {"Location": "http://www.sogou.com/antispider/?from=%2Fweb"}
        with self.assertRaises(SearxEngineCaptchaException):
            sogou.response(resp)

    def test_normal_response_is_parsed(self):
        resp = MagicMock()
        resp.status_code = 200
        resp.headers = {}
        resp.html.return_value = html.fromstring("<html><body></body></html>")
        self.assertEqual(sogou.response(resp), [])
