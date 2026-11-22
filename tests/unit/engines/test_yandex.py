# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name

import typing as t
from unittest.mock import patch

from searx.engines import yandex
from searx.search.processors import OnlineParams
from tests import SearxTestCase


class TestYandex(SearxTestCase):

    def test_request_allows_redirects(self):
        params = t.cast("OnlineParams", t.cast(object, {"pageno": 1, "searxng_locale": "en", "time_range": None}))
        with patch.object(yandex, "search_type", "web"):
            yandex.request("test", params)
        self.assertTrue(params["allow_redirects"])
        self.assertEqual(params["soft_max_redirects"], 1)
