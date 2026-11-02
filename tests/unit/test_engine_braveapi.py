# SPDX-License-Identifier: AGPL-3.0-or-later
"""Regression tests for the Brave Search API request headers."""

from parameterized import parameterized

from searx import engines
from searx.engines import braveapi
from searx.search.models import EngineRef, SearchQuery
from searx.search.processors.online import OnlineProcessor
from tests import SearxTestCase


class BraveApiEngineTests(SearxTestCase):
    """Brave API requests must satisfy the API's header validation."""

    @parameterized.expand([({},), ({"Cache-Control": "max-age=0"},)])
    def test_request_cache_control(self, headers: dict[str, str]):
        """Set no-cache even when an incompatible cache header is inherited."""
        engine_name = "dummy engine"
        query = SearchQuery("test", [EngineRef(engine_name, "general")], "all", 0, 1, None, None, None)
        params = OnlineProcessor(engines.engines[engine_name]).get_params(query, "general")
        assert params is not None
        params["headers"].update(headers)

        braveapi.request("test", params)

        self.assertEqual(params["headers"]["Cache-Control"], "no-cache")
