# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

import json
import unittest
from unittest.mock import Mock, patch, MagicMock

from searx.botdetection import abuseipdb


class AbuseIPDBCacheTests(unittest.TestCase):

    def test_cache_key(self):
        key = abuseipdb._cache_key("192.168.1.1")
        self.assertEqual(key, "abuseipdb:192.168.1.1")

        key = abuseipdb._cache_key("8.8.8.8")
        self.assertEqual(key, "abuseipdb:8.8.8.8")

    def test_get_cached_result(self):
        mock_client = MagicMock()
        mock_client.get.return_value = json.dumps({"abuseConfidenceScore": 50})

        result = abuseipdb._get_cached_result(mock_client, "8.8.8.8")

        self.assertEqual(result["abuseConfidenceScore"], 50)
        mock_client.get.assert_called_once_with("abuseipdb:8.8.8.8")

    def test_get_cached_result_missing(self):
        mock_client = MagicMock()
        mock_client.get.return_value = None

        result = abuseipdb._get_cached_result(mock_client, "8.8.8.8")

        self.assertIsNone(result)

    def test_get_cached_result_invalid_json(self):
        mock_client = MagicMock()
        mock_client.get.return_value = "invalid json"

        result = abuseipdb._get_cached_result(mock_client, "8.8.8.8")

        self.assertIsNone(result)

    def test_set_cached_result(self):
        mock_client = MagicMock()
        mock_client.setex = MagicMock()

        result = {"abuseConfidenceScore": 50}
        abuseipdb._set_cached_result(mock_client, "8.8.8.8", result, 3600)

        mock_client.setex.assert_called_once()
        args = mock_client.setex.call_args[0]
        self.assertEqual(args[0], "abuseipdb:8.8.8.8")
        self.assertEqual(args[1], 3600)
        self.assertEqual(json.loads(args[2]), result)


class AbuseIPDBCheckIPTests(unittest.TestCase):

    @patch("searx.botdetection.abuseipdb.requests.get")
    def test_check_ip_no_api_key(self, mock_get):
        mock_cfg = MagicMock()
        mock_cfg.get.return_value = ""

        result = abuseipdb.check_ip("8.8.8.8", mock_cfg)

        self.assertIsNone(result)
        mock_get.assert_not_called()

    @patch("searx.botdetection.abuseipdb.requests.get")
    def test_check_ip_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "ipAddress": "8.8.8.8",
                "abuseConfidenceScore": 50,
                "isTor": False,
            }
        }
        mock_get.return_value = mock_response

        mock_cfg = MagicMock()
        mock_cfg.get.return_value = "test_api_key"

        result = abuseipdb.check_ip("8.8.8.8", mock_cfg)

        self.assertIsNotNone(result)
        self.assertEqual(result["abuseConfidenceScore"], 50)
        self.assertFalse(result["isTor"])

    @patch("searx.botdetection.abuseipdb.requests.get")
    def test_check_ip_rate_limit(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        mock_cfg = MagicMock()
        mock_cfg.get.return_value = "test_api_key"

        result = abuseipdb.check_ip("8.8.8.8", mock_cfg)

        self.assertIsNone(result)

    @patch("searx.botdetection.abuseipdb.requests.get")
    def test_check_ip_api_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        mock_cfg = MagicMock()
        mock_cfg.get.return_value = "test_api_key"

        result = abuseipdb.check_ip("8.8.8.8", mock_cfg)

        self.assertIsNone(result)

    @patch("searx.botdetection.abuseipdb.requests.post")
    def test_report_ip(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"success": True}}
        mock_post.return_value = mock_response

        mock_cfg = MagicMock()
        mock_cfg.get.return_value = "test_api_key"

        result = abuseipdb.report_ip("192.168.1.1", "18", "Test report", mock_cfg)

        self.assertIsNotNone(result)
        self.assertTrue(result.get("success"))

    def test_report_ip_no_api_key(self):
        mock_cfg = MagicMock()
        mock_cfg.get.return_value = ""

        result = abuseipdb.report_ip("192.168.1.1", "18", "Test report", mock_cfg)

        self.assertIsNone(result)


class AbuseIPDBFilterRequestTests(unittest.TestCase):

    def test_filter_request_not_enabled(self):
        mock_cfg = MagicMock()
        mock_cfg.get.side_effect = lambda key, default=None: {
            "botdetection.abuseipdb.enabled": False,
        }.get(key, default)

        mock_network = MagicMock()
        mock_network.network_address = "8.8.8.8"
        mock_request = MagicMock()

        result = abuseipdb.filter_request(mock_network, mock_request, mock_cfg)

        self.assertIsNone(result)

    def test_filter_request_no_api_key(self):
        mock_cfg = MagicMock()
        mock_cfg.get.side_effect = lambda key, default=None: {
            "botdetection.abuseipdb.enabled": True,
            "botdetection.abuseipdb.api_key": "",
        }.get(key, default)

        mock_network = MagicMock()
        mock_network.network_address = "8.8.8.8"
        mock_request = MagicMock()

        result = abuseipdb.filter_request(mock_network, mock_request, mock_cfg)

        self.assertIsNone(result)

    @patch("searx.botdetection.abuseipdb._get_valkey_client")
    @patch("searx.botdetection.abuseipdb._get_cached_result")
    def test_filter_request_allows_low_score(self, mock_get_cached, mock_get_valkey):
        mock_valkey = MagicMock()
        mock_get_valkey.return_value = mock_valkey
        mock_get_cached.return_value = {"abuseConfidenceScore": 10, "isTor": False}

        mock_cfg = MagicMock()
        mock_cfg.get.side_effect = lambda key, default=None: {
            "botdetection.abuseipdb.enabled": True,
            "botdetection.abuseipdb.api_key": "test_key",
            "botdetection.abuseipdb.confidence_threshold": 75,
            "botdetection.abuseipdb.skip_tor": False,
            "botdetection.abuseipdb.cache_time": 3600,
        }.get(key, default)

        mock_network = MagicMock()
        mock_network.network_address = "8.8.8.8"
        mock_request = MagicMock()

        result = abuseipdb.filter_request(mock_network, mock_request, mock_cfg)

        self.assertIsNone(result)

    @patch("searx.botdetection.abuseipdb._get_valkey_client")
    @patch("searx.botdetection.abuseipdb._get_cached_result")
    def test_filter_request_blocks_high_score(self, mock_get_cached, mock_get_valkey):
        mock_valkey = MagicMock()
        mock_get_valkey.return_value = mock_valkey
        mock_get_cached.return_value = {"abuseConfidenceScore": 80, "isTor": False}

        mock_cfg = MagicMock()
        mock_cfg.get.side_effect = lambda key, default=None: {
            "botdetection.abuseipdb.enabled": True,
            "botdetection.abuseipdb.api_key": "test_key",
            "botdetection.abuseipdb.confidence_threshold": 75,
            "botdetection.abuseipdb.skip_tor": False,
            "botdetection.abuseipdb.cache_time": 3600,
        }.get(key, default)

        mock_network = MagicMock()
        mock_network.network_address = "8.8.8.8"
        mock_network.compressed = "8.8.8.8"
        mock_request = MagicMock()

        with patch("searx.botdetection.abuseipdb.flask.make_response") as mock_make_response:
            mock_make_response.return_value = MagicMock(status_code=429)
            result = abuseipdb.filter_request(mock_network, mock_request, mock_cfg)

        self.assertIsNotNone(result)

    @patch("searx.botdetection.abuseipdb._get_valkey_client")
    @patch("searx.botdetection.abuseipdb._get_cached_result")
    def test_filter_request_skips_tor_when_enabled(self, mock_get_cached, mock_get_valkey):
        mock_valkey = MagicMock()
        mock_get_valkey.return_value = mock_valkey
        mock_get_cached.return_value = {"abuseConfidenceScore": 80, "isTor": True}

        mock_cfg = MagicMock()
        mock_cfg.get.side_effect = lambda key, default=None: {
            "botdetection.abuseipdb.enabled": True,
            "botdetection.abuseipdb.api_key": "test_key",
            "botdetection.abuseipdb.confidence_threshold": 75,
            "botdetection.abuseipdb.skip_tor": True,
            "botdetection.abuseipdb.cache_time": 3600,
        }.get(key, default)

        mock_network = MagicMock()
        mock_network.network_address = "8.8.8.8"
        mock_request = MagicMock()

        result = abuseipdb.filter_request(mock_network, mock_request, mock_cfg)

        self.assertIsNone(result)

    @patch("searx.botdetection.abuseipdb._get_valkey_client")
    @patch("searx.botdetection.abuseipdb._get_cached_result")
    @patch("searx.botdetection.abuseipdb.check_ip")
    @patch("searx.botdetection.abuseipdb._set_cached_result")
    def test_filter_request_queries_api_when_not_cached(
        self, mock_set_cached, mock_check_ip, mock_get_cached, mock_get_valkey
    ):
        mock_valkey = MagicMock()
        mock_get_valkey.return_value = mock_valkey
        mock_get_cached.return_value = None
        mock_check_ip.return_value = {"abuseConfidenceScore": 20, "isTor": False}

        mock_cfg = MagicMock()
        mock_cfg.get.side_effect = lambda key, default=None: {
            "botdetection.abuseipdb.enabled": True,
            "botdetection.abuseipdb.api_key": "test_key",
            "botdetection.abuseipdb.confidence_threshold": 75,
            "botdetection.abuseipdb.skip_tor": False,
            "botdetection.abuseipdb.cache_time": 3600,
        }.get(key, default)

        mock_network = MagicMock()
        mock_network.network_address = "8.8.8.8"
        mock_request = MagicMock()

        result = abuseipdb.filter_request(mock_network, mock_request, mock_cfg)

        self.assertIsNone(result)
        mock_check_ip.assert_called_once()
        mock_set_cached.assert_called_once()

    @patch("searx.botdetection.abuseipdb._get_valkey_client")
    def test_filter_request_valkey_error(self, mock_get_valkey):
        mock_get_valkey.side_effect = Exception("Failed to connect")

        mock_cfg = MagicMock()
        mock_cfg.get.side_effect = lambda key, default=None: {
            "botdetection.abuseipdb.enabled": True,
            "botdetection.abuseipdb.api_key": "test_key",
        }.get(key, default)

        mock_network = MagicMock()
        mock_network.network_address = "8.8.8.8"
        mock_request = MagicMock()

        result = abuseipdb.filter_request(mock_network, mock_request, mock_cfg)

        self.assertIsNone(result)

    @patch("searx.botdetection.abuseipdb._get_valkey_client")
    @patch("searx.botdetection.abuseipdb._get_cached_result")
    @patch("searx.botdetection.abuseipdb.check_ip")
    def test_filter_request_api_failure_allows_request(
        self, mock_check_ip, mock_get_cached, mock_get_valkey
    ):
        mock_valkey = MagicMock()
        mock_get_valkey.return_value = mock_valkey
        mock_get_cached.return_value = None
        mock_check_ip.return_value = None

        mock_cfg = MagicMock()
        mock_cfg.get.side_effect = lambda key, default=None: {
            "botdetection.abuseipdb.enabled": True,
            "botdetection.abuseipdb.api_key": "test_key",
            "botdetection.abuseipdb.confidence_threshold": 75,
            "botdetection.abuseipdb.skip_tor": False,
            "botdetection.abuseipdb.cache_time": 3600,
        }.get(key, default)

        mock_network = MagicMock()
        mock_network.network_address = "8.8.8.8"
        mock_request = MagicMock()

        result = abuseipdb.filter_request(mock_network, mock_request, mock_cfg)

        self.assertIsNone(result)
