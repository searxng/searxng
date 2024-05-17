# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test module for the client and proxy handling code."""

from unittest.mock import patch, Mock

import httpx

from searx.network import client
from tests import SearxTestCase


class TestClient(SearxTestCase):
    """Tests for the client and proxy handling code."""

    def test_get_single_transport(self):
        t = client.get_single_transport(proxy_url="socks4://local:1080")
        self.assertTrue(isinstance(t, client.AsyncProxyTransportFixed))
        t = client.get_single_transport(proxy_url="socks5://local:1080")
        self.assertTrue(isinstance(t, client.AsyncProxyTransportFixed))
        t = client.get_single_transport(proxy_url="socks5h://local:1080")
        self.assertTrue(isinstance(t, client.AsyncProxyTransportFixed))
        t = client.get_single_transport(proxy_url="https://local:8080")
        self.assertTrue(isinstance(t, httpx.AsyncHTTPTransport))

    def test_get_parallel_transport(self):
        t = client.get_transport(
            proxy_urls=["socks5h://local:1080", "socks5h://local:1180"],
        )
        self.assertTrue(isinstance(t, client.AsyncParallelTransport))

    @patch(
        'searx.network.client.AsyncProxyTransportFixed.handle_async_request',
        side_effect=[httpx.Response(200, html="<html/>"), httpx.Response(301, html="<html/>")],
    )
    async def test_parallel_transport_ok(self, handler_mock: Mock):
        t = client.get_transport(
            proxy_urls=["socks5h://local:1080", "socks5h://local:1180"],
        )
        request = httpx.Request(url="http://wiki.com", method="GET")
        response = await t.handle_async_request(request)
        self.assertEqual(response.status_code, 200)
        handler_mock.assert_called_once_with(request)

        response = await t.handle_async_request(request)
        self.assertEqual(handler_mock.call_count, 2)
        self.assertEqual(response.status_code, 301)

    @patch(
        'searx.network.client.AsyncProxyTransportFixed.handle_async_request',
        side_effect=[httpx.Response(403, html="<html/>"), httpx.Response(200, html="<html/>")],
    )
    async def test_parallel_transport_403(self, handler_mock: Mock):
        t = client.get_transport(
            proxy_urls=["socks5h://local:1080", "socks5h://local:1180"],
            proxy_request_redundancy=2,
        )
        self.assertTrue(isinstance(t, client.AsyncParallelTransport))
        request = httpx.Request(url="http://wiki.com", method="GET")
        response = await t.handle_async_request(request)
        handler_mock.assert_called_with(request)
        self.assertEqual(handler_mock.call_count, 2)
        self.assertEqual(response.status_code, 200)

    @patch(
        'searx.network.client.AsyncProxyTransportFixed.handle_async_request',
        side_effect=[httpx.Response(404, html="<html/>"), httpx.Response(200, html="<html/>")],
    )
    async def test_parallel_transport_404(self, handler_mock: Mock):
        t = client.get_transport(
            proxy_urls=["socks5h://local:1080", "socks5h://local:1180"],
            proxy_request_redundancy=2,
        )
        self.assertTrue(isinstance(t, client.AsyncParallelTransport))
        request = httpx.Request(url="http://wiki.com", method="GET")
        response = await t.handle_async_request(request)
        handler_mock.assert_called_with(request)
        self.assertEqual(handler_mock.call_count, 2)
        self.assertEqual(response.status_code, 404)

    @patch(
        'searx.network.client.AsyncProxyTransportFixed.handle_async_request',
        side_effect=[httpx.Response(403, html="<html/>"), httpx.Response(403, html="<html/>")],
    )
    async def test_parallel_transport_403_403(self, handler_mock: Mock):
        t = client.get_transport(
            proxy_urls=["socks5h://local:1080", "socks5h://local:1180"],
            proxy_request_redundancy=2,
        )
        self.assertTrue(isinstance(t, client.AsyncParallelTransport))
        request = httpx.Request(url="http://wiki.com", method="GET")
        response = await t.handle_async_request(request)
        handler_mock.assert_called_with(request)
        self.assertEqual(handler_mock.call_count, 2)
        self.assertEqual(response.status_code, 403)

    @patch(
        'searx.network.client.AsyncProxyTransportFixed.handle_async_request',
        side_effect=[httpx.RequestError("OMG!"), httpx.Response(200, html="<html/>")],
    )
    async def test_parallel_transport_ex_ok(self, handler_mock: Mock):
        t = client.get_transport(
            proxy_urls=["socks5h://local:1080", "socks5h://local:1180"],
            proxy_request_redundancy=2,
        )
        self.assertTrue(isinstance(t, client.AsyncParallelTransport))
        request = httpx.Request(url="http://wiki.com", method="GET")
        response = await t.handle_async_request(request)
        handler_mock.assert_called_with(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(handler_mock.call_count, 2)

    @patch(
        'searx.network.client.AsyncProxyTransportFixed.handle_async_request',
        side_effect=[httpx.RequestError("OMG!"), httpx.RequestError("OMG!")],
    )
    async def test_parallel_transport_ex_ex(self, handler_mock: Mock):
        t = client.get_transport(
            proxy_urls=["socks5h://local:1080", "socks5h://local:1180"],
            proxy_request_redundancy=2,
        )
        self.assertTrue(isinstance(t, client.AsyncParallelTransport))
        request = httpx.Request(url="http://wiki.com", method="GET")
        response = None
        with self.assertRaises(httpx.RequestError):
            response = await t.handle_async_request(request)
        handler_mock.assert_called_with(request)
        self.assertFalse(response)
        self.assertEqual(handler_mock.call_count, 2)
