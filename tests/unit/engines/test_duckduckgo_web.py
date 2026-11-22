# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name,protected-access

from unittest.mock import MagicMock, patch

from lxml import html

from searx.engines import duckduckgo_web
from tests import SearxTestCase


class TestDuckDuckGoWeb(SearxTestCase):

    def test_first_page_request_sends_default_headers(self):
        dom = html.fromstring(
            '<html><head>'
            '<link id="deep_preload_link" href="https://links.duckduckgo.com/d.js?q=rust">'
            '</head></html>'
        )
        resp = MagicMock()
        resp.status_code = 200
        resp.html.return_value = dom

        cache = MagicMock()
        cache.get.return_value = None

        with (
            patch.object(duckduckgo_web, "CACHE", cache, create=True),
            patch.object(duckduckgo_web, "get", return_value=resp) as get_mock,
        ):
            link = duckduckgo_web._fetch_first_page_link("rust", {"Accept-Language": "en"})

        self.assertEqual(link, "https://links.duckduckgo.com/d.js?q=rust")
        get_mock.assert_called_once()
        self.assertTrue(get_mock.call_args.kwargs["default_headers"])
