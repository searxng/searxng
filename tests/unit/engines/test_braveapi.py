# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for the Brave Search API engine."""

from collections import defaultdict
from urllib.parse import parse_qs, urlparse

from searx.engines import braveapi

from tests import SearxTestCase


class TestBraveAPI(SearxTestCase):
    """Test Brave Search API request construction."""

    def setUp(self):
        self._api_key = braveapi.api_key
        self._results_per_page = braveapi.results_per_page
        braveapi.api_key = "test-api-key"
        braveapi.results_per_page = 20

    def tearDown(self):
        braveapi.api_key = self._api_key
        braveapi.results_per_page = self._results_per_page

    @staticmethod
    def _params(pageno):
        params = defaultdict(dict)
        params.update(
            {
                "pageno": pageno,
                "time_range": None,
                "safesearch": 0,
                "headers": {},
            }
        )
        return params

    def test_request_uses_zero_based_page_offset(self):
        """Brave expects offset to be the zero-based page number."""
        offsets = {}
        for pageno in (1, 2, 10):
            params = self._params(pageno)
            braveapi.request("test query", params)
            offsets[pageno] = int(parse_qs(urlparse(params["url"]).query)["offset"][0])

        self.assertEqual(offsets, {1: 0, 2: 1, 10: 9})

    def test_max_page_matches_brave_api_limit(self):
        """Brave accepts offsets 0 through 9, i.e. ten SearXNG pages."""
        self.assertEqual(braveapi.max_page, 10)
