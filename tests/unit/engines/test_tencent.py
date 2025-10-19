# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

from tests import SearxTestCase
from searx.engines import tencent
from unittest.mock import Mock
import json


class TestTencentEngine(SearxTestCase):
    """Test cases for Tencent Cloud Search engine"""

    def test_request(self):
        """Test request generation with valid credentials"""
        query = '北京天气'
        params = {'engine_settings': {'api_key': 'test_secret_id', 'secret_key': 'test_secret_key', 'mode': 0}}

        result = tencent.request(query, params)

        self.assertEqual(result['method'], 'POST')
        self.assertIn('wsa.tencentcloudapi.com', result['url'])
        self.assertIn('Authorization', result['headers'])
        self.assertIn('X-TC-Action', result['headers'])
        self.assertEqual(result['headers']['X-TC-Action'], 'SearchPro')

        # Check request body
        body = json.loads(result['data'])
        self.assertEqual(body['Query'], query)
        self.assertEqual(body['Mode'], 0)

    def test_request_without_credentials(self):
        """Test request without credentials returns None URL"""
        query = '测试'
        params = {'engine_settings': {}}

        result = tencent.request(query, params)

        self.assertIsNone(result['url'])

    def test_request_with_optional_params(self):
        """Test request with optional parameters"""
        query = '搜索'
        params = {
            'engine_settings': {
                'api_key': 'test_id',
                'secret_key': 'test_key',
                'mode': 2,
                'cnt': 30,
                'site': 'zhihu.com',
            }
        }

        result = tencent.request(query, params)

        body = json.loads(result['data'])
        self.assertEqual(body['Mode'], 2)
        self.assertEqual(body['Cnt'], 30)
        self.assertEqual(body['Site'], 'zhihu.com')

    def test_request_with_time_range(self):
        """Test request with time range parameters"""
        query = '新闻'
        params = {
            'engine_settings': {
                'api_key': 'test_id',
                'secret_key': 'test_key',
                'mode': 0,
                'from_time': '2024-01-01 00:00:00',
                'to_time': '2024-12-31 23:59:59',
            }
        }

        result = tencent.request(query, params)

        body = json.loads(result['data'])
        self.assertEqual(body['Query'], query)
        self.assertEqual(body['FromTime'], '2024-01-01 00:00:00')
        self.assertEqual(body['ToTime'], '2024-12-31 23:59:59')

    def test_request_with_partial_time_range(self):
        """Test request with only from_time parameter"""
        query = '历史'
        params = {
            'engine_settings': {
                'api_key': 'test_id',
                'secret_key': 'test_key',
                'mode': 0,
                'from_time': '2024-01-01 00:00:00',
            }
        }

        result = tencent.request(query, params)

        body = json.loads(result['data'])
        self.assertEqual(body['FromTime'], '2024-01-01 00:00:00')
        self.assertNotIn('ToTime', body)

    def test_request_with_all_optional_params(self):
        """Test request with all optional parameters combined"""
        query = '综合测试'
        params = {
            'engine_settings': {
                'api_key': 'test_id',
                'secret_key': 'test_key',
                'mode': 1,
                'cnt': 20,
                'site': 'example.com',
                'from_time': '2024-06-01 00:00:00',
                'to_time': '2024-12-31 23:59:59',
            }
        }

        result = tencent.request(query, params)

        body = json.loads(result['data'])
        self.assertEqual(body['Mode'], 1)
        self.assertEqual(body['Cnt'], 20)
        self.assertEqual(body['Site'], 'example.com')
        self.assertEqual(body['FromTime'], '2024-06-01 00:00:00')
        self.assertEqual(body['ToTime'], '2024-12-31 23:59:59')

    def test_response(self):
        """Test response parsing"""
        resp = Mock()
        resp.text = json.dumps(
            {
                "Response": {
                    "Pages": [
                        json.dumps(
                            {
                                "url": "https://example.com",
                                "title": "测试标题",
                                "passage": "测试摘要内容",
                                "site": "example.com",
                                "score": 0.95,
                                "date": "2025-10-18 10:00:00",
                            }
                        )
                    ],
                    "RequestId": "test-request-id",
                }
            }
        )

        results = tencent.response(resp)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['url'], 'https://example.com')
        self.assertEqual(results[0]['title'], '测试标题')
        self.assertEqual(results[0]['content'], '测试摘要内容')
        self.assertIn('example.com', results[0]['metadata'])
        self.assertIn('0.95', results[0]['metadata'])

    def test_response_with_error(self):
        """Test response with API error"""
        resp = Mock()
        resp.text = json.dumps({"Response": {"Error": {"Code": "AuthFailure", "Message": "Authentication failed"}}})

        with self.assertRaises(Exception) as context:
            tencent.response(resp)

        self.assertIn('AuthFailure', str(context.exception))

    def test_response_empty(self):
        """Test response with no results"""
        resp = Mock()
        resp.text = json.dumps({"Response": {"Pages": [], "RequestId": "test-id"}})

        results = tencent.response(resp)

        self.assertEqual(len(results), 0)

    def test_response_invalid_json(self):
        """Test response handles invalid JSON gracefully"""
        resp = Mock()
        resp.text = "invalid json"

        results = tencent.response(resp)

        self.assertEqual(len(results), 0)

    def test_signature_generation(self):
        """Test TC3-HMAC-SHA256 signature generation"""
        # This is a smoke test to ensure the signature function doesn't crash
        secret_id = "test_id"
        secret_key = "test_key"
        payload = '{"Query":"test","Mode":0}'
        timestamp = 1234567890

        try:
            auth = tencent.get_signature_v3(
                secret_id, secret_key, tencent.base_url.replace('https://', ''), payload, timestamp
            )
            self.assertIn('TC3-HMAC-SHA256', auth)
            self.assertIn('Credential=', auth)
            self.assertIn('Signature=', auth)
        except Exception as e:
            self.fail(f"Signature generation failed: {str(e)}")
