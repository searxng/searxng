# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

from curl_cffi.requests import Headers

from searx.engines import sogou
from searx.exceptions import SearxEngineCaptchaException
from searx.extended_types import SXNG_Response

from tests import SearxTestCase


def build_response(status_code: int, location: str | None = None) -> SXNG_Response:
    resp = SXNG_Response()
    resp.status_code = status_code
    resp.headers = Headers({"Location": location} if location else {})
    resp.content = b"<html><body></body></html>"
    return resp


class TestSogouEngine(SearxTestCase):

    def test_antispider_redirect(self):
        resp = build_response(302, "http://www.sogou.com/antispider/?from=%2Fweb%3Fquery%3Dtest")
        with self.assertRaises(SearxEngineCaptchaException):
            sogou.response(resp)

    def test_other_redirect(self):
        resp = build_response(302, "https://www.sogou.com/web?query=test")
        self.assertEqual(len(sogou.response(resp)), 0)
