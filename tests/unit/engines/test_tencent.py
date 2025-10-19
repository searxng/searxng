# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

import json
from tests import SearxTestCase
from searx.engines import tencent


class TestTencentEngine(SearxTestCase):
    """Test Tencent Cloud Web Search API engine"""

    def test_request_without_api_key(self):
        """Test that request returns None when API key is not configured"""
        # Save original values
        original_api_key = tencent.api_key
        original_secret_key = tencent.secret_key
        
        try:
            # Set empty API keys
            tencent.api_key = ''
            tencent.secret_key = ''
            
            params = tencent.request('test query', {})
            
            # Should return None URL when no API key
            self.assertIsNone(params['url'])
        finally:
            # Restore original values
            tencent.api_key = original_api_key
            tencent.secret_key = original_secret_key

    def test_request_with_api_key(self):
        """Test that request builds proper request when API key is configured"""
        # Save original values
        original_api_key = tencent.api_key
        original_secret_key = tencent.secret_key
        original_mode = tencent.mode
        original_cnt = tencent.cnt
        
        try:
            # Set test API keys
            tencent.api_key = 'test_id'
            tencent.secret_key = 'test_key'
            tencent.mode = 0
            tencent.cnt = 10
            
            params = tencent.request('test query', {})
            
            # Check request structure
            self.assertIsNotNone(params['url'])
            self.assertEqual(params['method'], 'POST')
            self.assertIn('Authorization', params['headers'])
            self.assertIn('X-TC-Action', params['headers'])
            self.assertEqual(params['headers']['X-TC-Action'], 'SearchPro')
            
            # Check payload
            payload = json.loads(params['data'])
            self.assertEqual(payload['Query'], 'test query')
            self.assertEqual(payload['Mode'], 0)
        finally:
            # Restore original values
            tencent.api_key = original_api_key
            tencent.secret_key = original_secret_key
            tencent.mode = original_mode
            tencent.cnt = original_cnt

    def test_response_parsing(self):
        """Test response parsing"""
        
        # Mock response
        class MockResponse:
            text = json.dumps({
                'Response': {
                    'Pages': [
                        json.dumps({
                            'url': 'https://example.com',
                            'title': 'Test Title',
                            'passage': 'Test content',
                            'site': 'example.com',
                            'score': 0.95,
                            'date': '2024-01-15'
                        })
                    ],
                    'RequestId': 'test-request-id'
                }
            })
        
        results = tencent.response(MockResponse())
        
        # Check results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['url'], 'https://example.com')
        self.assertEqual(results[0]['title'], 'Test Title')
        self.assertEqual(results[0]['content'], 'Test content')
        self.assertIn('example.com', results[0]['metadata'])
        self.assertIn('0.95', results[0]['metadata'])
        
        # Check date parsing
        self.assertIn('publishedDate', results[0])
        from datetime import datetime
        self.assertIsInstance(results[0]['publishedDate'], datetime)

    def test_response_error_handling(self):
        """Test error response handling"""
        
        # Mock error response
        class MockErrorResponse:
            text = json.dumps({
                'Response': {
                    'Error': {
                        'Code': 'AuthFailure',
                        'Message': 'Authentication failed'
                    }
                }
            })
        
        # Should raise ValueError for API errors
        with self.assertRaises(ValueError) as context:
            tencent.response(MockErrorResponse())
        
        self.assertIn('AuthFailure', str(context.exception))
        self.assertIn('Authentication failed', str(context.exception))
