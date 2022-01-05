# SPDX-License-Identifier: AGPL-3.0-or-later

from mock import patch

import httpx

from searx.network.network import Network, NETWORKS, initialize
from tests import SearxTestCase


class TestNetwork(SearxTestCase):
    def setUp(self):
        initialize()

    def test_simple(self):
        network = Network()

        self.assertEqual(next(network._local_addresses_cycle), None)
        self.assertEqual(next(network._proxies_cycle), ())

    def test_ipaddress_cycle(self):
        network = NETWORKS['ipv6']
        self.assertEqual(next(network._local_addresses_cycle), '::')
        self.assertEqual(next(network._local_addresses_cycle), '::')

        network = NETWORKS['ipv4']
        self.assertEqual(next(network._local_addresses_cycle), '0.0.0.0')
        self.assertEqual(next(network._local_addresses_cycle), '0.0.0.0')

        network = Network(local_addresses=['192.168.0.1', '192.168.0.2'])
        self.assertEqual(next(network._local_addresses_cycle), '192.168.0.1')
        self.assertEqual(next(network._local_addresses_cycle), '192.168.0.2')
        self.assertEqual(next(network._local_addresses_cycle), '192.168.0.1')

        network = Network(local_addresses=['192.168.0.0/30'])
        self.assertEqual(next(network._local_addresses_cycle), '192.168.0.1')
        self.assertEqual(next(network._local_addresses_cycle), '192.168.0.2')
        self.assertEqual(next(network._local_addresses_cycle), '192.168.0.1')
        self.assertEqual(next(network._local_addresses_cycle), '192.168.0.2')

        network = Network(local_addresses=['fe80::/10'])
        self.assertEqual(next(network._local_addresses_cycle), 'fe80::1')
        self.assertEqual(next(network._local_addresses_cycle), 'fe80::2')
        self.assertEqual(next(network._local_addresses_cycle), 'fe80::3')

        with self.assertRaises(ValueError):
            Network(local_addresses=['not_an_ip_address'])

    def test_proxy_cycles(self):
        network = Network(proxies='http://localhost:1337')
        self.assertEqual(next(network._proxies_cycle), (('all://', 'http://localhost:1337'),))

        network = Network(proxies={'https': 'http://localhost:1337', 'http': 'http://localhost:1338'})
        self.assertEqual(
            next(network._proxies_cycle), (('https://', 'http://localhost:1337'), ('http://', 'http://localhost:1338'))
        )
        self.assertEqual(
            next(network._proxies_cycle), (('https://', 'http://localhost:1337'), ('http://', 'http://localhost:1338'))
        )

        network = Network(
            proxies={'https': ['http://localhost:1337', 'http://localhost:1339'], 'http': 'http://localhost:1338'}
        )
        self.assertEqual(
            next(network._proxies_cycle), (('https://', 'http://localhost:1337'), ('http://', 'http://localhost:1338'))
        )
        self.assertEqual(
            next(network._proxies_cycle), (('https://', 'http://localhost:1339'), ('http://', 'http://localhost:1338'))
        )

        with self.assertRaises(ValueError):
            Network(proxies=1)

    def test_get_kwargs_clients(self):
        kwargs = {
            'verify': True,
            'max_redirects': 5,
            'timeout': 2,
            'allow_redirects': True,
        }
        kwargs_client = Network.extract_kwargs_clients(kwargs)

        self.assertEqual(len(kwargs_client), 2)
        self.assertEqual(len(kwargs), 2)

        self.assertEqual(kwargs['timeout'], 2)
        self.assertEqual(kwargs['follow_redirects'], True)

        self.assertTrue(kwargs_client['verify'])
        self.assertEqual(kwargs_client['max_redirects'], 5)

    async def test_get_client(self):
        network = Network(verify=True)
        client1 = await network.get_client()
        client2 = await network.get_client(verify=True)
        client3 = await network.get_client(max_redirects=10)
        client4 = await network.get_client(verify=True)
        client5 = await network.get_client(verify=False)
        client6 = await network.get_client(max_redirects=10)

        self.assertEqual(client1, client2)
        self.assertEqual(client1, client4)
        self.assertNotEqual(client1, client3)
        self.assertNotEqual(client1, client5)
        self.assertEqual(client3, client6)

        await network.aclose()

    async def test_aclose(self):
        network = Network(verify=True)
        await network.get_client()
        await network.aclose()

    async def test_request(self):
        a_text = 'Lorem Ipsum'
        response = httpx.Response(status_code=200, text=a_text)
        with patch.object(httpx.AsyncClient, 'request', return_value=response):
            network = Network(enable_http=True)
            response = await network.request('GET', 'https://example.com/')
            self.assertEqual(response.text, a_text)
            await network.aclose()


class TestNetworkRequestRetries(SearxTestCase):

    TEXT = 'Lorem Ipsum'

    @classmethod
    def get_response_404_then_200(cls):
        first = True

        async def get_response(*args, **kwargs):
            nonlocal first
            if first:
                first = False
                return httpx.Response(status_code=403, text=TestNetworkRequestRetries.TEXT)
            return httpx.Response(status_code=200, text=TestNetworkRequestRetries.TEXT)

        return get_response

    async def test_retries_ok(self):
        with patch.object(httpx.AsyncClient, 'request', new=TestNetworkRequestRetries.get_response_404_then_200()):
            network = Network(enable_http=True, retries=1, retry_on_http_error=403)
            response = await network.request('GET', 'https://example.com/')
            self.assertEqual(response.text, TestNetworkRequestRetries.TEXT)
            await network.aclose()

    async def test_retries_fail_int(self):
        with patch.object(httpx.AsyncClient, 'request', new=TestNetworkRequestRetries.get_response_404_then_200()):
            network = Network(enable_http=True, retries=0, retry_on_http_error=403)
            response = await network.request('GET', 'https://example.com/')
            self.assertEqual(response.status_code, 403)
            await network.aclose()

    async def test_retries_fail_list(self):
        with patch.object(httpx.AsyncClient, 'request', new=TestNetworkRequestRetries.get_response_404_then_200()):
            network = Network(enable_http=True, retries=0, retry_on_http_error=[403, 429])
            response = await network.request('GET', 'https://example.com/')
            self.assertEqual(response.status_code, 403)
            await network.aclose()

    async def test_retries_fail_bool(self):
        with patch.object(httpx.AsyncClient, 'request', new=TestNetworkRequestRetries.get_response_404_then_200()):
            network = Network(enable_http=True, retries=0, retry_on_http_error=True)
            response = await network.request('GET', 'https://example.com/')
            self.assertEqual(response.status_code, 403)
            await network.aclose()

    async def test_retries_exception_then_200(self):
        request_count = 0

        async def get_response(*args, **kwargs):
            nonlocal request_count
            request_count += 1
            if request_count < 3:
                raise httpx.RequestError('fake exception', request=None)
            return httpx.Response(status_code=200, text=TestNetworkRequestRetries.TEXT)

        with patch.object(httpx.AsyncClient, 'request', new=get_response):
            network = Network(enable_http=True, retries=2)
            response = await network.request('GET', 'https://example.com/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.text, TestNetworkRequestRetries.TEXT)
            await network.aclose()

    async def test_retries_exception(self):
        async def get_response(*args, **kwargs):
            raise httpx.RequestError('fake exception', request=None)

        with patch.object(httpx.AsyncClient, 'request', new=get_response):
            network = Network(enable_http=True, retries=0)
            with self.assertRaises(httpx.RequestError):
                await network.request('GET', 'https://example.com/')
            await network.aclose()


class TestNetworkStreamRetries(SearxTestCase):

    TEXT = 'Lorem Ipsum'

    @classmethod
    def get_response_exception_then_200(cls):
        first = True

        def stream(*args, **kwargs):
            nonlocal first
            if first:
                first = False
                raise httpx.RequestError('fake exception', request=None)
            return httpx.Response(status_code=200, text=TestNetworkStreamRetries.TEXT)

        return stream

    async def test_retries_ok(self):
        with patch.object(httpx.AsyncClient, 'stream', new=TestNetworkStreamRetries.get_response_exception_then_200()):
            network = Network(enable_http=True, retries=1, retry_on_http_error=403)
            response = await network.stream('GET', 'https://example.com/')
            self.assertEqual(response.text, TestNetworkStreamRetries.TEXT)
            await network.aclose()

    async def test_retries_fail(self):
        with patch.object(httpx.AsyncClient, 'stream', new=TestNetworkStreamRetries.get_response_exception_then_200()):
            network = Network(enable_http=True, retries=0, retry_on_http_error=403)
            with self.assertRaises(httpx.RequestError):
                await network.stream('GET', 'https://example.com/')
            await network.aclose()

    async def test_retries_exception(self):
        first = True

        def stream(*args, **kwargs):
            nonlocal first
            if first:
                first = False
                return httpx.Response(status_code=403, text=TestNetworkRequestRetries.TEXT)
            return httpx.Response(status_code=200, text=TestNetworkRequestRetries.TEXT)

        with patch.object(httpx.AsyncClient, 'stream', new=stream):
            network = Network(enable_http=True, retries=0, retry_on_http_error=403)
            response = await network.stream('GET', 'https://example.com/')
            self.assertEqual(response.status_code, 403)
            await network.aclose()
