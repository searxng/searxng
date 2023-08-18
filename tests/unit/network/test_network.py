# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=unused-argument
# pylint: disable=missing-class-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-function-args
"""
Test for searx.network (what a surprise)
"""


from typing import Optional
import time

from mock import patch
from parameterized import parameterized, parameterized_class
import httpx

import searx.network
import searx.network.context
from searx import settings
from searx.network.client import BaseHTTPClient, HTTPClient, TorHTTPClient, _HTTPMultiClientConf
from searx.network.network import Network, NETWORKS
from tests import SearxTestCase


class TestHTTPClient(SearxTestCase):
    def test_get_client(self):
        httpclient = BaseHTTPClient(verify=True)
        client1 = httpclient._get_client_and_update_kwargs({})
        client2 = httpclient._get_client_and_update_kwargs({"verify": True})
        client3 = httpclient._get_client_and_update_kwargs({"max_redirects": 10})
        client4 = httpclient._get_client_and_update_kwargs({"verify": True})
        client5 = httpclient._get_client_and_update_kwargs({"verify": False})
        client6 = httpclient._get_client_and_update_kwargs({"max_redirects": 10})

        self.assertEqual(client1, client2)
        self.assertEqual(client1, client4)
        self.assertNotEqual(client1, client3)
        self.assertNotEqual(client1, client5)
        self.assertEqual(client3, client6)

        httpclient.close()


class TestNetwork(SearxTestCase):
    def setUp(self):
        NETWORKS.initialize_from_settings(settings_engines=settings["engines"], settings_outgoing=settings["outgoing"])

    def test_simple(self):
        network = Network.from_dict()

        self.assertEqual(next(network._local_addresses_cycle), None)
        self.assertEqual(next(network._proxies_cycle), ())

    def test_ipaddress_cycle(self):
        network = NETWORKS.get('ipv6')
        self.assertEqual(next(network._local_addresses_cycle), '::')
        self.assertEqual(next(network._local_addresses_cycle), '::')

        network = NETWORKS.get('ipv4')
        self.assertEqual(next(network._local_addresses_cycle), '0.0.0.0')
        self.assertEqual(next(network._local_addresses_cycle), '0.0.0.0')

        network = Network.from_dict(local_addresses=['192.168.0.1', '192.168.0.2'])
        self.assertEqual(next(network._local_addresses_cycle), '192.168.0.1')
        self.assertEqual(next(network._local_addresses_cycle), '192.168.0.2')
        self.assertEqual(next(network._local_addresses_cycle), '192.168.0.1')

        network = Network.from_dict(local_addresses=['192.168.0.0/30'])
        self.assertEqual(next(network._local_addresses_cycle), '192.168.0.1')
        self.assertEqual(next(network._local_addresses_cycle), '192.168.0.2')
        self.assertEqual(next(network._local_addresses_cycle), '192.168.0.1')
        self.assertEqual(next(network._local_addresses_cycle), '192.168.0.2')

        network = Network.from_dict(local_addresses=['fe80::/10'])
        self.assertEqual(next(network._local_addresses_cycle), 'fe80::1')
        self.assertEqual(next(network._local_addresses_cycle), 'fe80::2')
        self.assertEqual(next(network._local_addresses_cycle), 'fe80::3')

        with self.assertRaises(ValueError):
            Network.from_dict(local_addresses=['not_an_ip_address'])

    def test_proxy_cycles(self):
        network = Network.from_dict(proxies='http://localhost:1337')
        self.assertEqual(next(network._proxies_cycle), (('all://', 'http://localhost:1337'),))

        network = Network.from_dict(proxies={'https': 'http://localhost:1337', 'http': 'http://localhost:1338'})
        self.assertEqual(
            next(network._proxies_cycle), (('https://', 'http://localhost:1337'), ('http://', 'http://localhost:1338'))
        )
        self.assertEqual(
            next(network._proxies_cycle), (('https://', 'http://localhost:1337'), ('http://', 'http://localhost:1338'))
        )

        network = Network.from_dict(
            proxies={'https': ['http://localhost:1337', 'http://localhost:1339'], 'http': 'http://localhost:1338'}
        )
        self.assertEqual(
            next(network._proxies_cycle), (('https://', 'http://localhost:1337'), ('http://', 'http://localhost:1338'))
        )
        self.assertEqual(
            next(network._proxies_cycle), (('https://', 'http://localhost:1339'), ('http://', 'http://localhost:1338'))
        )

        with self.assertRaises(ValueError):
            Network.from_dict(proxies=1)

    def test_get_kwargs_clients(self):
        kwargs = {
            'verify': True,
            'max_redirects': 5,
            'timeout': 2,
            'allow_redirects': True,
        }
        kwargs_client, kwargs = BaseHTTPClient()._extract_kwargs_clients(kwargs)

        self.assertEqual(len(kwargs), 2)
        self.assertEqual(kwargs['timeout'], 2)
        self.assertEqual(kwargs['allow_redirects'], True)

        self.assertIsInstance(kwargs_client, _HTTPMultiClientConf)
        self.assertTrue(kwargs_client.verify)
        self.assertEqual(kwargs_client.max_redirects, 5)

    def test_close(self):
        network = Network.from_dict(verify=True)
        network._get_http_client()
        network.close()

    def test_request(self):
        a_text = 'Lorem Ipsum'
        response = httpx.Response(status_code=200, text=a_text)
        with patch.object(httpx.Client, 'request', return_value=response):
            network = Network.from_dict(enable_http=True)
            http_client = network._get_http_client()
            response = http_client.request('GET', 'https://example.com/')
            self.assertEqual(response.text, a_text)
            network.close()


@parameterized_class(
    [
        {"RETRY_STRATEGY": "ENGINE"},
        {"RETRY_STRATEGY": "SAME_HTTP_CLIENT"},
        {"RETRY_STRATEGY": "DIFFERENT_HTTP_CLIENT"},
    ]
)
class TestNetworkRequestRetries(SearxTestCase):

    TEXT = "Lorem Ipsum"
    RETRY_STRATEGY = "ENGINE"

    @classmethod
    def get_response_403_then_200(cls):
        first = True

        def get_response(*args, **kwargs):
            nonlocal first
            request = httpx.Request('GET', 'http://localhost')
            if first:
                first = False
                return httpx.Response(status_code=403, text=TestNetworkRequestRetries.TEXT, request=request)
            return httpx.Response(status_code=200, text=TestNetworkRequestRetries.TEXT, request=request)

        return get_response

    def test_retries_ok(self):
        with patch.object(httpx.Client, 'request', new=TestNetworkRequestRetries.get_response_403_then_200()):
            network = Network.from_dict(
                enable_http=True, retries=1, retry_on_http_error=403, retry_strategy=self.RETRY_STRATEGY
            )
            context = network.get_context(timeout=3600.0)
            response = context.request('GET', 'https://example.com/', raise_for_httperror=False)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.text, TestNetworkRequestRetries.TEXT)
            network.close()

    def test_retries_fail_int(self):
        with patch.object(httpx.Client, 'request', new=TestNetworkRequestRetries.get_response_403_then_200()):
            network = Network.from_dict(
                enable_http=True, retries=0, retry_on_http_error=403, retry_strategy=self.RETRY_STRATEGY
            )
            context = network.get_context(timeout=2.0)
            response = context.request('GET', 'https://example.com/', raise_for_httperror=False)
            self.assertEqual(response.status_code, 403)
            network.close()

    def test_retries_fail_list(self):
        with patch.object(httpx.Client, 'request', new=TestNetworkRequestRetries.get_response_403_then_200()):
            network = Network.from_dict(
                enable_http=True, retries=0, retry_on_http_error=[403, 429], retry_strategy=self.RETRY_STRATEGY
            )
            context = network.get_context(timeout=2.0)
            response = context.request('GET', 'https://example.com/', raise_for_httperror=False)
            self.assertEqual(response.status_code, 403)
            network.close()

    def test_retries_fail_bool(self):
        with patch.object(httpx.Client, 'request', new=TestNetworkRequestRetries.get_response_403_then_200()):
            network = Network.from_dict(
                enable_http=True, retries=0, retry_on_http_error=True, retry_strategy=self.RETRY_STRATEGY
            )
            context = network.get_context(timeout=2.0)
            response = context.request('GET', 'https://example.com/', raise_for_httperror=False)
            self.assertEqual(response.status_code, 403)
            network.close()

    def test_retries_exception_then_200(self):
        request_count = 0

        def get_response(*args, **kwargs):
            nonlocal request_count
            request_count += 1
            if request_count <= 2:
                raise httpx.RequestError('fake exception', request=None)
            return httpx.Response(status_code=200, text=TestNetworkRequestRetries.TEXT)

        with patch.object(httpx.Client, 'request', new=get_response):
            network = Network.from_dict(enable_http=True, retries=3, retry_strategy=self.RETRY_STRATEGY)
            context = network.get_context(timeout=2.0)
            response = context.request('GET', 'https://example.com/', raise_for_httperror=False)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.text, TestNetworkRequestRetries.TEXT)
            network.close()

    def test_retries_exception(self):
        def get_response(*args, **kwargs):
            raise httpx.RequestError('fake exception', request=None)

        with patch.object(httpx.Client, 'request', new=get_response):
            network = Network.from_dict(enable_http=True, retries=0, retry_strategy=self.RETRY_STRATEGY)
            context = network.get_context(timeout=2.0)
            with self.assertRaises(httpx.RequestError):
                context.request('GET', 'https://example.com/', raise_for_httperror=False)
            network.close()


class TestNetworkStreamRetries(SearxTestCase):

    TEXT = 'Lorem Ipsum'

    @classmethod
    def get_response_exception_then_200(cls):
        from httpx import SyncByteStream  # pylint: disable=import-outside-toplevel

        first = True

        class FakeStream(SyncByteStream):
            def __iter__(self):
                yield TestNetworkStreamRetries.TEXT.encode()

        def send(*args, **kwargs):
            nonlocal first
            if first:
                first = False
                raise httpx.RequestError('fake exception', request=None)
            return httpx.Response(status_code=200, stream=FakeStream())

        return send

    def test_retries_ok(self):
        with patch.object(httpx.Client, 'send', new=TestNetworkStreamRetries.get_response_exception_then_200()):
            network = Network.from_dict(enable_http=True, retries=1, retry_on_http_error=403)
            context = network.get_context(timeout=3600.0)
            response = context.stream('GET', 'https://example.com/')
            btext = b"".join(btext for btext in response.iter_bytes())
            self.assertEqual(btext.decode(), TestNetworkStreamRetries.TEXT)
            response.close()
            network.close()

    def test_retries_fail(self):
        with patch.object(httpx.Client, 'send', new=TestNetworkStreamRetries.get_response_exception_then_200()):
            network = Network.from_dict(enable_http=True, retries=0, retry_on_http_error=403)
            context = network.get_context(timeout=2.0)
            with self.assertRaises(httpx.RequestError):
                context.stream('GET', 'https://example.com/')
            network.close()

    def test_retries_exception(self):
        first = True

        def send(*args, **kwargs):
            nonlocal first
            if first:
                first = False
                return httpx.Response(status_code=403, text=TestNetworkRequestRetries.TEXT)
            return httpx.Response(status_code=200, text=TestNetworkRequestRetries.TEXT)

        with patch.object(httpx.Client, 'send', new=send):
            network = Network.from_dict(enable_http=True, retries=0, retry_on_http_error=403)
            context = network.get_context(timeout=2.0)
            response = context.stream('GET', 'https://example.com/', raise_for_httperror=False)
            self.assertEqual(response.status_code, 403)
            network.close()


class TestNetworkApi(SearxTestCase):

    TEXT = 'Lorem Ipsum'

    def test_no_networkcontext(self):
        with self.assertRaises(searx.network.NetworkContextNotFound):
            searx.network.request("GET", "https://example.com")

    def test_provide_networkcontext(self):
        send_was_called = False
        response = None

        def send(*args, **kwargs):
            nonlocal send_was_called
            send_was_called = True
            return httpx.Response(status_code=200, text=TestNetworkApi.TEXT)

        @searx.network.networkcontext_decorator()
        def main():
            nonlocal response
            response = searx.network.get("https://example.com")

        with patch.object(httpx.Client, 'send', new=send):
            main()

        self.assertTrue(send_was_called)
        self.assertIsInstance(response, httpx.Response)
        self.assertEqual(response.text, TestNetworkApi.TEXT)

    @parameterized.expand(
        [
            ("OPTIONS",),
            ("HEAD",),
            ("DELETE",),
        ]
    )
    def test_options(self, method):
        send_was_called = False
        request: Optional[httpx.Request] = None
        response = None

        def send(_, actual_request: httpx.Request, **kwargs):
            nonlocal request, send_was_called
            request = actual_request
            send_was_called = True
            return httpx.Response(status_code=200, text=TestNetworkApi.TEXT)

        @searx.network.networkcontext_decorator()
        def main():
            nonlocal response
            f = getattr(searx.network, method.lower())
            response = f("https://example.com", params={"a": "b"}, headers={"c": "d"})

        with patch.object(httpx.Client, 'send', new=send):
            main()

        self.assertTrue(send_was_called)
        self.assertIsInstance(response, httpx.Response)
        self.assertEqual(request.method, method)
        self.assertEqual(request.url, "https://example.com?a=b")
        self.assertEqual(request.headers["c"], "d")
        self.assertEqual(response.text, TestNetworkApi.TEXT)

    @parameterized.expand(
        [
            ("POST",),
            ("PUT",),
            ("PATCH",),
        ]
    )
    def test_post(self, method):
        send_was_called = False
        request: Optional[httpx.Request] = None
        response = None

        data = "this_is_data"

        def send(_, actual_request: httpx.Request, **kwargs):
            nonlocal request, send_was_called
            request = actual_request
            send_was_called = True
            return httpx.Response(status_code=200, text=TestNetworkApi.TEXT)

        @searx.network.networkcontext_decorator()
        def main():
            nonlocal response
            f = getattr(searx.network, method.lower())
            response = f("https://example.com", params={"a": "b"}, headers={"c": "d"}, data=data)

        with patch.object(httpx.Client, 'send', new=send):
            main()

        self.assertTrue(send_was_called)
        self.assertIsInstance(response, httpx.Response)
        self.assertEqual(request.method, method)
        self.assertEqual(request.url, "https://example.com?a=b")
        self.assertEqual(request.headers["c"], "d")
        self.assertEqual(request.content, data.encode())
        self.assertEqual(response.text, TestNetworkApi.TEXT)

    def test_get_remaining_time(self):
        def send(*args, **kwargs):
            time.sleep(0.25)
            return httpx.Response(status_code=200, text=TestNetworkApi.TEXT)

        with patch.object(httpx.Client, 'send', new=send):
            with searx.network.networkcontext_manager(timeout=3.0) as network_context:
                network_context.request("GET", "https://example.com")
                network_context.get_http_runtime()
                self.assertTrue(network_context.get_http_runtime() > 0.25)
                overhead = 0.2  # see NetworkContext.get_remaining_time
                self.assertTrue(network_context.get_remaining_time() < (2.75 + overhead))


class TestNetworkRepr(SearxTestCase):
    def test_repr(self):
        network = Network.from_dict(logger_name="test", retry_strategy="ENGINE")
        network_context = network.get_context(5.0)
        network_context._set_http_client()
        http_client = network_context._get_http_client()

        r_network = repr(network)
        r_network_context = repr(network_context)
        r_http_client = repr(http_client)

        self.assertEqual(r_network, "<Network logger_name='test'>")
        self.assertTrue(r_network_context.startswith("<NetworkContextRetryFunction retries=0 timeout=5.0 "))
        self.assertTrue(r_network_context.endswith("network_context=<Network logger_name='test'>>"))
        self.assertTrue(r_http_client.startswith("<searx.network.context._RetryFunctionHTTPClient"))

    def test_repr_no_network(self):
        def http_client_factory():
            return HTTPClient()

        network_context = searx.network.context.NetworkContextRetryFunction(3, http_client_factory, 1.0, 2.0)
        r_network_context = repr(network_context)
        self.assertTrue(
            r_network_context.startswith("<NetworkContextRetryFunction retries=3 timeout=2.0 http_client=None")
        )


class TestTorHTTPClient(SearxTestCase):

    API_RESPONSE_FALSE = '{"IsTor":false,"IP":"42.42.42.42"}'
    API_RESPONSE_TRUE = '{"IsTor":true,"IP":"42.42.42.42"}'

    @parameterized.expand(
        [
            ({"all://": "socks5://localhost:4000"},),
            ({"all://": "socks5h://localhost:4000"},),
            ({"all://": "http://localhost:5000"},),
            ({"all://": "https://localhost:5000"},),
            (None,),
        ]
    )
    def test_without_tor(self, proxies):
        check_done = False

        def send(*args, **kwargs):
            nonlocal check_done
            return httpx.Response(status_code=200, text=TestTorHTTPClient.API_RESPONSE_FALSE)

        with patch.object(httpx.Client, 'send', new=send):
            TorHTTPClient._clear_cache()
            TorHTTPClient._TOR_CHECK_RESULT = {}
            with self.assertRaises(httpx.HTTPError):
                TorHTTPClient(proxies=proxies)
                self.assertTrue(check_done)

    @parameterized.expand(
        [
            ("socks5h://localhost:8888",),
        ]
    )
    def test_with_tor(self, proxy_url):
        check_count = 0

        def send(*args, **kwargs):
            nonlocal check_count
            check_count += 1
            return httpx.Response(status_code=200, text=TestTorHTTPClient.API_RESPONSE_TRUE)

        with patch.object(httpx.Client, 'send', new=send):
            proxies = {
                "all://": proxy_url,
            }
            TorHTTPClient._clear_cache()
            TorHTTPClient(proxies=proxies, enable_http=False)
            TorHTTPClient(proxies=proxies, enable_http=False)
            self.assertEqual(check_count, 1)
