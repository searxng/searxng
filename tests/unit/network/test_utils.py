# SPDX-License-Identifier: AGPL-3.0-or-later

import random
from yarl import URL

from searx.network.utils import URLPattern
from searx.testing import SearxTestCase


class TestNetworkUtils(SearxTestCase):
    def test_pattern_priority(self):
        matchers = [
            URLPattern("all://"),
            URLPattern("http://"),
            URLPattern("http://example.com"),
            URLPattern("http://example.com:123"),
        ]
        random.shuffle(matchers)
        self.maxDiff = None
        self.assertEqual(
            sorted(matchers),
            [
                URLPattern("http://example.com:123"),
                URLPattern("http://example.com"),
                URLPattern("http://"),
                URLPattern("all://"),
            ],
        )

    def test_url_matches(self):
        parameters = [
            ("http://example.com", "http://example.com", True),
            ("http://example.com", "https://example.com", False),
            ("http://example.com", "http://other.com", False),
            ("http://example.com:123", "http://example.com:123", True),
            ("http://example.com:123", "http://example.com:456", False),
            ("http://example.com:123", "http://example.com", False),
            ("all://example.com", "http://example.com", True),
            ("all://example.com", "https://example.com", True),
            ("http://", "http://example.com", True),
            ("http://", "https://example.com", False),
            ("all://", "https://example.com:123", True),
            ("", "https://example.com:123", True),
        ]

        for pattern, url, expected in parameters:
            pattern = URLPattern(pattern)
            self.assertEqual(pattern.matches(URL(url)), expected)
