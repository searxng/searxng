# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

import re

from parameterized.parameterized import parameterized

from searx.plugins import hostnames
from searx.result_types import MainResult
from tests import SearxTestCase


class PluginHostnameReplaceTest(SearxTestCase):
    @parameterized.expand(
        [
            (
                {re.compile(r".*.baz\.com")},
                {},
                [
                    ("https://baz.com", True),
                    ("https://foo.baz.com", False),
                ],
            ),
            (
                set(),
                {
                    re.compile(r"example\.com"): "example.org",
                },
                [
                    ("https://example.com", "https://example.org"),
                    ("https://foo.example.com", "https://foo.example.org"),
                    ("https://example.net", True),
                ],
            ),
            (
                set(),
                {
                    re.compile(r"(?P<subdomain>.*)\.foo\.bar"): "foo.bar/<subdomain>",
                },
                [
                    ("https://sub.foo.bar", "https://foo.bar/sub"),
                    ("https://foo.bar", True),
                ],
            ),
        ],
    )
    def test_filter_url_field(
        self, remove: set[re.Pattern], replace: dict[re.Pattern, str], test_cases: list[tuple[str, str]]
    ):
        hostnames.REMOVE = remove
        hostnames.REPLACE = replace

        for input_url, expected_result in test_cases:
            result = hostnames.filter_url_field(MainResult(url=input_url), "url", input_url)
            self.assertEqual(result, expected_result)
