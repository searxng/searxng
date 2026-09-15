# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for the Easylist adblock rules parser.
"""

import urllib.parse
from parameterized import parameterized

from searx.easylist import parse, EasylistFilterRule
from tests import SearxTestCase


class TestEasylistParser(SearxTestCase):
    """
    Test class for testing the Easylist adblock rules parser.
    """

    @parameterized.expand(
        [
            ("@@||example.com", "https://example.com", True),
            ("@@||example.com", "https://foo.example.com", False),
            ("svg|", "https://example.com/foo.svg", True),
            ("svg|", "https://example.com/svg.foo", False),
            ("@@example.co^", "https://example.co/path", True),
            ("@@example.co^", "https://example.co.uk", False),
            ("://*.example.com/", "https://foo.example.com/foo", True),
            ("://*.example.com/", "https://example.com/foo", False),
            ("|http://example.com", "http://example.com", True),
            ("|http://example.com", "https://example.com", False),
            ("||example.com/@username^$doc", "https://example.com/@username/about", True),
            ("||example.com/@username^$doc", "https://foo.example.com/@username/about", False),
        ]
    )
    def test_parse_rule(self, rule: str, url: str, should_match: bool):
        parsed_rule = parse(rule)
        self.assertIsInstance(parsed_rule, EasylistFilterRule)
        parsed_url = urllib.parse.urlparse(url)
        if parsed_rule:
            self.assertEqual(parsed_rule.matches_url(parsed_url), should_match)
