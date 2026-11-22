# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name

import typing as t
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from searx.engines import openalex
from searx.search.processors import OnlineParams
from tests import SearxTestCase


class TestOpenAlex(SearxTestCase):

    @staticmethod
    def _params() -> OnlineParams:
        return t.cast("OnlineParams", t.cast(object, {"pageno": 1, "language": "en"}))

    def test_api_key_is_sent(self):
        with patch.object(openalex, "api_key", "KEY123"):
            params = self._params()
            openalex.request("test", params)
        query = parse_qs(urlparse(str(params["url"])).query)
        self.assertEqual(query["api_key"], ["KEY123"])

    def test_mailto_fallback(self):
        with patch.object(openalex, "api_key", ""), patch.object(openalex, "mailto", "a@b.c"):
            params = self._params()
            openalex.request("test", params)
        query = parse_qs(urlparse(str(params["url"])).query)
        self.assertEqual(query["mailto"], ["a@b.c"])
        self.assertNotIn("api_key", query)

    def test_no_authentication(self):
        with patch.object(openalex, "api_key", ""), patch.object(openalex, "mailto", ""):
            params = self._params()
            openalex.request("test", params)
        query = parse_qs(urlparse(str(params["url"])).query)
        self.assertNotIn("api_key", query)
        self.assertNotIn("mailto", query)
