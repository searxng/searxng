# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring

from searx.metrics import counter_inc, initialize, openmetrics
from tests import SearxTestCase


class OpenMetricsTestCase(SearxTestCase):

    def test_engine_request_counters(self):
        engine_name = "test-engine"
        initialize([engine_name])
        for _ in range(3):
            counter_inc("engine", engine_name, "search", "count", "successful")
        for _ in range(2):
            counter_inc("engine", engine_name, "search", "count", "error")

        metrics = openmetrics(
            {
                "time": [
                    {
                        "name": engine_name,
                        "total": 0,
                        "processing": 0,
                        "http": 0,
                        "result_count": 0,
                    }
                ]
            },
            {engine_name: {"sent_count": 5, "reliability": 60}},
        )

        self.assertIn(
            "# TYPE searxng_engines_successful_request_count_total counter\n"
            'searxng_engines_successful_request_count_total{engine_name="test-engine"} 3\n',
            metrics,
        )
        self.assertIn(
            "# TYPE searxng_engines_error_request_count_total counter\n"
            'searxng_engines_error_request_count_total{engine_name="test-engine"} 2\n',
            metrics,
        )
