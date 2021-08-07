# SPDX-License-Identifier: AGPL-3.0-or-later

import asyncio
from searx.network.utils import URLPattern
from mock import patch

import aiohttp
from multidict import CIMultiDict, CIMultiDictProxy
import yarl

from searx.network.network import Network, NETWORKS, initialize
from searx.testing import SearxTestCase


def create_fake_response(url, method='GET', content='', status_code=200):
    if isinstance(url, str):
        url = yarl.URL(url)
    if not isinstance(url, yarl.URL):
        raise ValueError('url must be of type yarl.URL. Currently of type ' + str(type(url)))
    loop = asyncio.get_event_loop()
    request_info = aiohttp.RequestInfo(
        url,
        method,
        CIMultiDictProxy(CIMultiDict()),
        url
    )
    response = aiohttp.ClientResponse(
        method,
        url,
        writer=None,
        continue100=False,
        timer=None,
        request_info=request_info,
        traces=[],
        loop=loop,
        session=None
    )

    async def async_nothing():
        pass

    def iter_content(_):
        yield content.encode()

    response.status = status_code
    response._headers = {}
    response.read = async_nothing
    response.close = lambda: None
    response.release = async_nothing
    response.content = content.encode()
    response._body = response.content
    response.get_encoding = lambda: 'utf-8'
    response.iter_content = iter_content
    return response


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
        P = URLPattern
        self.assertEqual(next(network._proxies_cycle), ((P('all://'), 'http://localhost:1337'),))

        network = Network(proxies={
            'https': 'http://localhost:1337',
            'http': 'http://localhost:1338'
        })
        self.assertEqual(next(network._proxies_cycle),
                         ((P('https://'), 'http://localhost:1337'), (P('http://'), 'http://localhost:1338')))
        self.assertEqual(next(network._proxies_cycle),
                         ((P('https://'), 'http://localhost:1337'), (P('http://'), 'http://localhost:1338')))

        network = Network(proxies={
            'https': ['http://localhost:1337', 'http://localhost:1339'],
            'http': 'http://localhost:1338'
        })
        self.assertEqual(next(network._proxies_cycle),
                         ((P('https://'), 'http://localhost:1337'), (P('http://'), 'http://localhost:1338')))
        self.assertEqual(next(network._proxies_cycle),
                         ((P('https://'), 'http://localhost:1339'), (P('http://'), 'http://localhost:1338')))

        with self.assertRaises(ValueError):
            Network(proxies=1)

    def test_get_kwargs_clients(self):
        kwargs = {
            'verify': True,
        }
        kwargs_client = Network.get_kwargs_clients(kwargs)

        self.assertEqual(len(kwargs_client), 1)
        self.assertEqual(len(kwargs), 0)

        self.assertTrue(kwargs_client['verify'])

    async def test_get_client(self):
        network = Network(verify=True)
        url = 'https://example.com'
        client1 = network.get_client(url)
        client2 = network.get_client(url, verify=True)
        client3 = network.get_client(url, verify=False)

        self.assertEqual(client1, client2)
        self.assertNotEqual(client1, client3)

        await network.aclose()

    async def test_aclose(self):
        network = Network(verify=True)
        network.get_client('https://example.com')
        await network.aclose()

    async def test_request(self):
        a_text = 'Lorem Ipsum'

        async def get_response(*args, **kwargs):
            return create_fake_response(url='https://example.com/', status_code=200, content=a_text)

        with patch.object(aiohttp.ClientSession, 'request', new=get_response):
            network = Network(enable_http=True)
            response = await network.request('GET', 'https://example.com/')
            self.assertEqual(response.text, a_text)
            await network.aclose()


class TestNetworkRequestRetries(SearxTestCase):

    TEXT = 'Lorem Ipsum'

    @classmethod
    def get_response_404_then_200(cls):
        first = True

        async def get_response(method, url, *args, **kwargs):
            nonlocal first
            if first:
                first = False
                return create_fake_response(
                    method=method,
                    url=url,
                    status_code=403,
                    content=TestNetworkRequestRetries.TEXT
                )
            return create_fake_response(
                method=method,
                url=url,
                status_code=200,
                content=TestNetworkRequestRetries.TEXT
            )
        return get_response

    async def test_retries_ok(self):
        with patch.object(aiohttp.ClientSession, 'request', new=TestNetworkRequestRetries.get_response_404_then_200()):
            network = Network(enable_http=True, retries=1, retry_on_http_error=403)
            response = await network.request('GET', 'https://example.com/')
            self.assertEqual(response.text, TestNetworkRequestRetries.TEXT)
            await network.aclose()

    async def test_retries_fail_int(self):
        with patch.object(aiohttp.ClientSession, 'request', new=TestNetworkRequestRetries.get_response_404_then_200()):
            network = Network(enable_http=True, retries=0, retry_on_http_error=403)
            response = await network.request('GET', 'https://example.com/')
            self.assertEqual(response.status_code, 403)
            await network.aclose()

    async def test_retries_fail_list(self):
        with patch.object(aiohttp.ClientSession, 'request', new=TestNetworkRequestRetries.get_response_404_then_200()):
            network = Network(enable_http=True, retries=0, retry_on_http_error=[403, 429])
            response = await network.request('GET', 'https://example.com/')
            self.assertEqual(response.status_code, 403)
            await network.aclose()

    async def test_retries_fail_bool(self):
        with patch.object(aiohttp.ClientSession, 'request', new=TestNetworkRequestRetries.get_response_404_then_200()):
            network = Network(enable_http=True, retries=0, retry_on_http_error=True)
            response = await network.request('GET', 'https://example.com/')
            self.assertEqual(response.status_code, 403)
            await network.aclose()

    async def test_retries_exception_then_200(self):
        request_count = 0

        async def get_response(method, url, *args, **kwargs):
            nonlocal request_count
            request_count += 1
            if request_count < 3:
                raise aiohttp.ClientError()
            return create_fake_response(
                url,
                method,
                status_code=200,
                content=TestNetworkRequestRetries.TEXT
            )

        with patch.object(aiohttp.ClientSession, 'request', new=get_response):
            network = Network(enable_http=True, retries=2)
            response = await network.request('GET', 'https://example.com/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.text, TestNetworkRequestRetries.TEXT)
            await network.aclose()

    async def test_retries_exception(self):
        def get_response(*args, **kwargs):
            raise aiohttp.ClientError()

        with patch.object(aiohttp.ClientSession, 'request', new=get_response):
            network = Network(enable_http=True, retries=0)
            with self.assertRaises(aiohttp.ClientError):
                await network.request('GET', 'https://example.com/')
            await network.aclose()


class TestNetworkStreamRetries(SearxTestCase):

    TEXT = 'Lorem Ipsum'

    @classmethod
    def get_response_exception_then_200(cls):
        first = True

        async def stream(method, url, *args, **kwargs):
            nonlocal first
            if first:
                first = False
                raise aiohttp.ClientError()
            return create_fake_response(url, method, content=TestNetworkStreamRetries.TEXT, status_code=200)
        return stream

    async def test_retries_ok(self):
        with patch.object(
            aiohttp.ClientSession,
            'request',
            new=TestNetworkStreamRetries.get_response_exception_then_200()
        ):
            network = Network(enable_http=True, retries=1, retry_on_http_error=403)
            response = await network.request('GET', 'https://example.com/', read_response=False)
            self.assertEqual(response.text, TestNetworkStreamRetries.TEXT)
            await network.aclose()

    async def test_retries_fail(self):
        with patch.object(
            aiohttp.ClientSession,
            'request',
            new=TestNetworkStreamRetries.get_response_exception_then_200()
        ):
            network = Network(enable_http=True, retries=0, retry_on_http_error=403)
            with self.assertRaises(aiohttp.ClientError):
                await network.request('GET', 'https://example.com/', read_response=False)
            await network.aclose()

    async def test_retries_exception(self):
        first = True

        async def request(method, url, *args, **kwargs):
            nonlocal first
            if first:
                first = False
                return create_fake_response(url, method, status_code=403, content=TestNetworkRequestRetries.TEXT)
            return create_fake_response(url, method, status_code=200, content=TestNetworkRequestRetries.TEXT)

        with patch.object(aiohttp.ClientSession, 'request', new=request):
            network = Network(enable_http=True, retries=0, retry_on_http_error=403)
            response = await network.request('GET', 'https://example.com/', read_response=False)
            self.assertEqual(response.status_code, 403)
            await network.aclose()
