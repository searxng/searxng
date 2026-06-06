# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring

import logging
from datetime import datetime
from unittest.mock import Mock
from parameterized import parameterized

import searx.search
import searx.engines
from tests import SearxTestCase


class NvdTests(SearxTestCase):

    TEST_SETTINGS = "test_nvd.yml"

    def setUp(self):
        super().setUp()
        self.nvd = searx.engines.engines['nvd']
        self.nvd.logger.setLevel(logging.INFO)

    def tearDown(self):
        searx.search.load_engines([])

    @parameterized.expand(
        [
            ("1999-03-22T05:00:00.000", datetime(1999, 3, 22, 5, 0, 0)),
            ("1999-03-22T05:00:00", datetime(1999, 3, 22, 5, 0, 0)),
        ]
    )
    def test_published_date_parses_isoformat_variants(self, published, expected):
        response = Mock()
        response.json.return_value = {
            "response": [
                {
                    "grid": {
                        "vulnerabilities": [
                            {
                                "cve": {
                                    "id": "CVE-1999-0001",
                                    "published": published,
                                    "descriptions": [{"value": "Test vulnerability"}],
                                    "metrics": {},
                                }
                            }
                        ]
                    }
                }
            ]
        }

        results = self.nvd.response(response)

        self.assertEqual(expected, results[0]["publishedDate"])
