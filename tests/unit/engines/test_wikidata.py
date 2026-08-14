# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring

import sys
import unittest
from unittest import mock

if "pwd" not in sys.modules:
    sys.modules["pwd"] = mock.MagicMock()

from searx.engines import wikidata
from searx.version import VERSION_TAG
from searx.data import WIKIDATA_UNITS
from tests import SearxTestCase


class TestWikidataEngine(SearxTestCase):

    def setUp(self):
        super().setUp()
        # Ensure fresh CACHE mock
        wikidata.CACHE = mock.MagicMock()

    def test_get_headers_wikimedia_compliance(self):
        headers = wikidata.get_headers()
        self.assertEqual(headers.get("Accept"), "application/sparql-results+json")
        expected_ua = f"SearXNG/{VERSION_TAG} (https://github.com/searxng/searxng; contact@searxng.org) wikidata-engine"
        self.assertEqual(headers.get("User-Agent"), expected_ua)

    def test_init_wikidata_properties_success(self):
        wikidata.CACHE.get.return_value = None
        fake_response = {
            "results": {
                "bindings": [
                    {
                        "item": {"value": "http://www.wikidata.org/entity/P1082"},
                        "name": {"value": "population", "xml:lang": "en"},
                    }
                ]
            }
        }

        with mock.patch(
            "searx.engines.wikidata.send_wikidata_query", return_value=fake_response
        ):
            wikidata.init_wikidata_properties()

        # Check unit mappings added
        for k, v in WIKIDATA_UNITS.items():
            self.assertEqual(wikidata.WIKIDATA_PROPERTIES[k], v["symbol"])

        # Check property added from query
        self.assertEqual(
            wikidata.WIKIDATA_PROPERTIES.get(("P1082", "en")), "Population"
        )
        wikidata.CACHE.set.assert_called_once_with(
            key="WIKIDATA_PROPERTIES", value=wikidata.WIKIDATA_PROPERTIES
        )

    def test_init_wikidata_properties_network_failure_fallback(self):
        wikidata.CACHE.get.return_value = None

        with mock.patch(
            "searx.engines.wikidata.send_wikidata_query",
            side_effect=Exception("HTTP 403 Forbidden: Wikimedia policy"),
        ):
            # Should not raise exception and log a warning
            wikidata.init_wikidata_properties()

        # Units should still be populated
        for k, v in WIKIDATA_UNITS.items():
            self.assertEqual(wikidata.WIKIDATA_PROPERTIES[k], v["symbol"])

        wikidata.CACHE.set.assert_called_once_with(
            key="WIKIDATA_PROPERTIES", value=wikidata.WIKIDATA_PROPERTIES
        )

    def test_init_wikidata_properties_cached(self):
        cached_props = {"P434": "MusicBrainz", "cached_key": "cached_val"}
        wikidata.CACHE.get.return_value = cached_props

        with mock.patch("searx.engines.wikidata.send_wikidata_query") as mock_query:
            wikidata.init_wikidata_properties()
            mock_query.assert_not_called()

        self.assertEqual(wikidata.WIKIDATA_PROPERTIES, cached_props)

    def test_request_headers(self):
        params = {"searxng_locale": "en-US"}
        wikidata.traits = mock.MagicMock()
        wikidata.traits.get_region.return_value = "en"
        wikidata.traits.get_language.return_value = "en"
        wikidata.traits.custom = {"wiki_netloc": {}}

        wikidata.request("Alan Turing", params)

        self.assertEqual(params["method"], "POST")
        self.assertEqual(params["url"], wikidata.SPARQL_ENDPOINT_URL)
        self.assertIn("headers", params)
        expected_ua = f"SearXNG/{VERSION_TAG} (https://github.com/searxng/searxng; contact@searxng.org) wikidata-engine"
        self.assertEqual(params["headers"].get("User-Agent"), expected_ua)
        self.assertEqual(
            params["headers"].get("Accept"), "application/sparql-results+json"
        )

    def test_get_label_for_entity(self):
        wikidata.WIKIDATA_PROPERTIES = {
            "P345": "IMDb",
            ("P1082", "en"): "Population",
            ("P1082", "fr"): "Population (FR)",
        }
        self.assertEqual(wikidata.get_label_for_entity("P345", "en"), "IMDb")
        self.assertEqual(wikidata.get_label_for_entity("P1082", "en"), "Population")
        self.assertEqual(
            wikidata.get_label_for_entity("P1082", "fr-FR"), "Population (FR)"
        )
        self.assertEqual(wikidata.get_label_for_entity("P1082", "de"), "Population")
        self.assertEqual(
            wikidata.get_label_for_entity("UNKNOWN_PROP", "en"), "UNKNOWN_PROP"
        )
