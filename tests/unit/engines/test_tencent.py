# SPDX-License-Identifier: AGPL-3.0-or-later
"""Unit tests for Tencent Cloud Web Search API engine"""

from unittest.mock import Mock
from searx.engines import tencent
from tests import SearxTestCase


class TestTencentEngine(SearxTestCase):
    """Test class for Tencent engine"""

    def setUp(self):
        """Set up test fixtures"""
        # Save original values
        self.orig_api_key = tencent.api_key
        self.orig_secret_key = tencent.secret_key
        
        # Set test configuration (required params only)
        tencent.api_key = 'test_api_key'
        tencent.secret_key = 'test_secret_key'

    def tearDown(self):
        """Clean up after tests"""
        # Restore original values
        tencent.api_key = self.orig_api_key
        tencent.secret_key = self.orig_secret_key
        
        # Clean up any optional params that were set during tests
        for attr in ['mode', 'cnt', 'site', 'from_time', 'to_time']:
            if hasattr(tencent, attr):
                delattr(tencent, attr)

    def test_request_with_valid_credentials(self):
        """Test request building with valid API credentials"""
        query = 'test query'
        params = {
            'url': None,
            'method': 'GET',
            'headers': {},
            'data': {},
        }
        
        result = tencent.request(query, params)
        
        # Check that request was built correctly
        self.assertIsNotNone(result['url'])
        self.assertEqual(result['url'], 'https://wsa.tencentcloudapi.com/')
        self.assertEqual(result['method'], 'POST')
        self.assertIn('Authorization', result['headers'])
        self.assertIn('X-TC-Action', result['headers'])
        self.assertEqual(result['headers']['X-TC-Action'], 'SearchPro')
        self.assertEqual(result['headers']['X-TC-Version'], '2025-05-08')

    def test_request_without_credentials(self):
        """Test request building without API credentials"""
        tencent.api_key = ''
        tencent.secret_key = ''
        
        query = 'test query'
        params = {
            'url': None,
            'method': 'GET',
            'headers': {},
            'data': {},
        }
        
        result = tencent.request(query, params)
        
        # Check that no URL is generated
        self.assertIsNone(result['url'])

    def test_response_parsing(self):
        """Test response parsing"""
        from datetime import datetime
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'Response': {
                'RequestId': 'test-request-id',
                'Query': 'test query',
                'Pages': [
                    '{"url":"https://example.com/1","title":"Test Result 1","passage":"Test content 1","score":0.95,"date":"2025-10-04 05:00:47"}',
                    '{"url":"https://example.com/2","title":"Test Result 2","content":"Test content 2","score":0.85}',
                ]
            }
        }
        
        results = tencent.response(mock_response)
        
        # Check results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['url'], 'https://example.com/1')
        self.assertEqual(results[0]['title'], 'Test Result 1')
        self.assertEqual(results[0]['content'], 'Test content 1')
        # Check that date was parsed correctly
        self.assertIsInstance(results[0]['publishedDate'], datetime)
        self.assertEqual(results[0]['publishedDate'].year, 2025)
        
        self.assertEqual(results[1]['url'], 'https://example.com/2')
        self.assertEqual(results[1]['title'], 'Test Result 2')
        # Second result has no date
        self.assertNotIn('publishedDate', results[1])

    def test_response_with_error(self):
        """Test response parsing with API error"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'Response': {
                'Error': {
                    'Code': 'InvalidParameter',
                    'Message': 'Invalid parameter value'
                }
            }
        }
        
        with self.assertRaises(ValueError) as context:
            tencent.response(mock_response)
        
        self.assertIn('InvalidParameter', str(context.exception))

    def test_response_with_invalid_json(self):
        """Test response parsing with invalid JSON"""
        import json
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError('Invalid JSON', '', 0)
        
        results = tencent.response(mock_response)
        
        # Should return empty results on JSON decode error
        self.assertEqual(len(results), 0)

    def test_request_with_optional_params(self):
        """Test request building with optional parameters"""
        # Set optional parameters
        tencent.mode = 1
        tencent.cnt = 50
        tencent.site = 'example.com'
        tencent.from_time = 20180101  # YYYYMMDD format will be converted to timestamp
        tencent.to_time = 20181231
        
        query = 'test query'
        params = {
            'url': None,
            'method': 'GET',
            'headers': {},
            'data': {},
        }
        
        result = tencent.request(query, params)
        
        # Check that request includes optional params
        self.assertIsNotNone(result['data'])
        import json
        request_body = json.loads(result['data'])
        self.assertEqual(request_body['Mode'], 1)
        self.assertEqual(request_body['Cnt'], 50)
        self.assertEqual(request_body['Site'], 'example.com')
        # Verify time values were converted to Unix timestamps
        self.assertIsInstance(request_body['FromTime'], int)
        self.assertIsInstance(request_body['ToTime'], int)
        # FromTime should be > 1000000000 (Unix timestamp), not 20180101
        self.assertGreater(request_body['FromTime'], 1000000000)
        self.assertGreater(request_body['ToTime'], 1000000000)
    
    def test_request_with_defaults(self):
        """Test request building uses default values when optional params not set"""
        query = 'test query'
        params = {
            'url': None,
            'method': 'GET',
            'headers': {},
            'data': {},
        }
        
        result = tencent.request(query, params)
        
        # Check that defaults are used
        self.assertIsNotNone(result['data'])
        import json
        request_body = json.loads(result['data'])
        self.assertEqual(request_body['Mode'], 0)  # Default mode
        self.assertNotIn('Cnt', request_body)  # Default cnt (10) not added to body
        self.assertNotIn('Site', request_body)
        self.assertNotIn('FromTime', request_body)
        self.assertNotIn('ToTime', request_body)
    
    def test_response_with_invalid_date(self):
        """Test response parsing with invalid date format"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'Response': {
                'RequestId': 'test-request-id',
                'Query': 'test query',
                'Pages': [
                    '{"url":"https://example.com/1","title":"Test Result","passage":"Content","date":"invalid-date"}',
                ]
            }
        }
        
        results = tencent.response(mock_response)
        
        # Should still return result, just without publishedDate
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['url'], 'https://example.com/1')
        self.assertNotIn('publishedDate', results[0])
    
    def test_request_with_url_params(self):
        """Test request building with URL parameters (engine_data)"""
        query = 'test query'
        params = {
            'url': None,
            'method': 'GET',
            'headers': {},
            'data': {},
            # Simulate URL parameters: ?engine_data-tencent-mode=2&engine_data-tencent-cnt=20&engine_data-tencent-site=example.com
            'engine_data': {
                'mode': '2',
                'cnt': '20',
                'site': 'example.com',
                'from_time': '20180101',  # YYYYMMDD will be converted to timestamp
                'to_time': '20181231',
            }
        }
        
        result = tencent.request(query, params)
        
        # Check that URL params are used and time values are converted to Unix timestamps
        self.assertIsNotNone(result['data'])
        import json
        request_body = json.loads(result['data'])
        self.assertEqual(request_body['Mode'], 2)
        self.assertEqual(request_body['Cnt'], 20)
        self.assertEqual(request_body['Site'], 'example.com')
        # Verify YYYYMMDD was converted to Unix timestamp
        self.assertGreater(request_body['FromTime'], 1000000000)
        self.assertGreater(request_body['ToTime'], 1000000000)
        # FromTime should be less than ToTime
        self.assertLess(request_body['FromTime'], request_body['ToTime'])
    
    def test_timestamp_conversion(self):
        """Test that YYYYMMDD format is correctly converted to Unix timestamp"""
        query = 'test query'
        params = {
            'url': None,
            'method': 'GET',
            'headers': {},
            'data': {},
            'engine_data': {
                'from_time': '20180101',  # 2018-01-01 00:00:00 UTC
                'to_time': '20180101',    # 2018-01-01 23:59:59 UTC
            }
        }
        
        result = tencent.request(query, params)
        
        import json
        from datetime import datetime, timezone
        request_body = json.loads(result['data'])
        
        # Verify conversion
        # 20180101 00:00:00 UTC = 1514764800
        expected_from = int(datetime(2018, 1, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp())
        # 20180101 23:59:59 UTC = 1514851199
        expected_to = int(datetime(2018, 1, 1, 23, 59, 59, tzinfo=timezone.utc).timestamp())
        
        self.assertEqual(request_body['FromTime'], expected_from)
        self.assertEqual(request_body['ToTime'], expected_to)
    
    def test_unix_timestamp_passthrough(self):
        """Test that Unix timestamps are passed through without conversion"""
        query = 'test query'
        params = {
            'url': None,
            'method': 'GET',
            'headers': {},
            'data': {},
            'engine_data': {
                'from_time': '1514764800',  # Already a Unix timestamp
                'to_time': '1546300799',
            }
        }
        
        result = tencent.request(query, params)
        
        import json
        request_body = json.loads(result['data'])
        
        # Should be passed through unchanged
        self.assertEqual(request_body['FromTime'], 1514764800)
        self.assertEqual(request_body['ToTime'], 1546300799)
    
    def test_url_params_override_config(self):
        """Test that URL parameters override settings.yml configuration"""
        # Set config values
        tencent.mode = 0
        tencent.cnt = 10
        tencent.site = 'config-site.com'
        
        query = 'test query'
        params = {
            'url': None,
            'method': 'GET',
            'headers': {},
            'data': {},
            # URL params should override config
            'engine_data': {
                'mode': '2',
                'cnt': '50',
                'site': 'url-site.com',
            }
        }
        
        result = tencent.request(query, params)
        
        # URL params should take priority
        import json
        request_body = json.loads(result['data'])
        self.assertEqual(request_body['Mode'], 2)  # from URL, not 0 from config
        self.assertEqual(request_body['Cnt'], 50)  # from URL, not 10 from config
        self.assertEqual(request_body['Site'], 'url-site.com')  # from URL, not config-site.com
