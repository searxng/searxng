# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

from tests import SearxTestCase
from searx.engines import alphavantage
from unittest.mock import Mock


class TestAlphaVantageEngine(SearxTestCase):
    """Test cases for Alpha Vantage engine"""

    def test_request(self):
        """Test request generation"""
        query = 'AAPL'
        params = {'engine_settings': {'api_key': 'test_key'}}

        result = alphavantage.request(query, params)

        self.assertEqual(result['method'], 'GET')
        self.assertEqual(result['url'], alphavantage.base_url)
        self.assertEqual(result['data']['function'], 'SYMBOL_SEARCH')
        self.assertEqual(result['data']['keywords'], query)
        self.assertEqual(result['data']['apikey'], 'test_key')

    def test_request_without_api_key(self):
        """Test request without API key returns None URL"""
        query = 'AAPL'
        params = {'engine_settings': {}}

        result = alphavantage.request(query, params)

        self.assertIsNone(result['url'])

    def test_response(self):
        """Test response parsing"""
        resp = Mock()
        resp.json = lambda: {
            "bestMatches": [
                {
                    "1. symbol": "AAPL",
                    "2. name": "Apple Inc",
                    "3. type": "Equity",
                    "4. region": "United States",
                    "8. currency": "USD",
                    "9. matchScore": "1.0000",
                }
            ]
        }

        results = alphavantage.response(resp)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'AAPL - Apple Inc')
        self.assertIn('Equity', results[0]['content'])
        self.assertIn('United States', results[0]['content'])
        self.assertIn('USD', results[0]['content'])

    def test_response_with_error(self):
        """Test response with API error"""
        resp = Mock()
        resp.json = lambda: {"Error Message": "Invalid API call"}

        results = alphavantage.response(resp)

        self.assertEqual(len(results), 0)

    def test_response_with_note(self):
        """Test response with API limit note"""
        resp = Mock()
        resp.json = lambda: {"Note": "API call frequency exceeded"}

        results = alphavantage.response(resp)

        self.assertEqual(len(results), 0)

    def test_response_exception(self):
        """Test response handles exceptions gracefully"""
        resp = Mock()
        resp.json = lambda: None

        results = alphavantage.response(resp)

        self.assertEqual(len(results), 0)
