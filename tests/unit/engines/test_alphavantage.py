# SPDX-License-Identifier: AGPL-3.0-or-later
"""Unit tests for Alpha Vantage engine"""

from unittest.mock import Mock
from searx.engines import alphavantage
from tests import SearxTestCase


class TestAlphaVantageEngine(SearxTestCase):
    """Test class for Alpha Vantage engine"""

    def setUp(self):
        """Set up test fixtures"""
        # Save original value
        self.orig_api_key = alphavantage.api_key
        
        # Set test configuration
        alphavantage.api_key = 'test_api_key'

    def tearDown(self):
        """Clean up after tests"""
        # Restore original value
        alphavantage.api_key = self.orig_api_key
    
    def test_setup_with_valid_key(self):
        """Test setup function with valid API key"""
        engine_settings = {
            'api_key': 'TEST_API_KEY_123',
        }
        
        result = alphavantage.setup(engine_settings)
        
        # Should return True and set global variable
        self.assertTrue(result)
        self.assertEqual(alphavantage.api_key, 'TEST_API_KEY_123')
    
    def test_setup_without_key(self):
        """Test setup function without API key"""
        engine_settings = {}
        
        result = alphavantage.setup(engine_settings)
        
        # Should return False (engine will be disabled)
        self.assertFalse(result)
    
    def test_setup_with_placeholder_key(self):
        """Test setup function with placeholder API key"""
        engine_settings = {
            'api_key': 'YOUR_API_KEY',  # Placeholder value
        }
        
        result = alphavantage.setup(engine_settings)
        
        # Should return False (placeholder not accepted)
        self.assertFalse(result)

    def test_request_with_valid_key(self):
        """Test request building with valid API key"""
        query = 'AAPL'
        params = {
            'url': None,
            'method': 'GET',
            'data': {},
        }
        
        result = alphavantage.request(query, params)
        
        # Check that request was built correctly
        self.assertEqual(result['url'], 'https://www.alphavantage.co/query')
        self.assertEqual(result['method'], 'GET')
        self.assertEqual(result['data']['function'], 'SYMBOL_SEARCH')
        self.assertEqual(result['data']['keywords'], 'AAPL')
        self.assertEqual(result['data']['apikey'], 'test_api_key')

    def test_request_without_key(self):
        """Test request building without API key"""
        alphavantage.api_key = ''
        
        query = 'AAPL'
        params = {
            'url': None,
            'method': 'GET',
            'data': {},
        }
        
        result = alphavantage.request(query, params)
        
        # Check that no URL is generated
        self.assertIsNone(result['url'])

    def test_response_parsing(self):
        """Test response parsing"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'bestMatches': [
                {
                    '1. symbol': 'AAPL',
                    '2. name': 'Apple Inc',
                    '3. type': 'Equity',
                    '4. region': 'United States',
                    '8. currency': 'USD',
                    '9. matchScore': '1.0000',
                },
                {
                    '1. symbol': 'AAPL.TRT',
                    '2. name': 'Apple CDR',
                    '3. type': 'Equity',
                    '4. region': 'Toronto',
                    '8. currency': 'CAD',
                    '9. matchScore': '0.7273',
                },
            ]
        }
        
        results = alphavantage.response(mock_response)
        
        # Check results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['title'], 'AAPL - Apple Inc')
        self.assertEqual(results[0]['content'], 'Equity | United States | USD')
        self.assertEqual(results[0]['url'], 'https://finance.yahoo.com/quote/AAPL')
        self.assertIn('Match Score', results[0]['metadata'])

    def test_response_with_error(self):
        """Test response parsing with API error"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'Error Message': 'Invalid API key'
        }
        
        results = alphavantage.response(mock_response)
        
        # Should return empty results
        self.assertEqual(len(results), 0)

    def test_response_with_rate_limit(self):
        """Test response parsing with rate limit"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'Note': 'Thank you for using Alpha Vantage! Our standard API rate limit is...'
        }
        
        results = alphavantage.response(mock_response)
        
        # Should return empty results
        self.assertEqual(len(results), 0)
