# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=global-statement
# pylint: disable=missing-module-docstring, missing-class-docstring

import atexit
import asyncio
import ipaddress
from itertools import cycle
from typing import Dict

import httpx

from searx import logger, searx_debug
from .client import new_client, get_loop, AsyncHTTPTransportNoHttp


logger = logger.getChild('network')
DEFAULT_NAME = '__DEFAULT__'
NETWORKS: Dict[str, 'Network'] = {}
# requests compatibility when reading proxy settings from settings.yml
PROXY_PATTERN_MAPPING = {
    'http': 'http://',
    'https': 'https://',
    'socks4': 'socks4://',
    'socks5': 'socks5://',
    'socks5h': 'socks5h://',
    'http:': 'http://',
    'https:': 'https://',
    'socks4:': 'socks4://',
    'socks5:': 'socks5://',
    'socks5h:': 'socks5h://',
}

ADDRESS_MAPPING = {'ipv4': '0.0.0.0', 'ipv6': '::'}


class Network:

    __slots__ = (
        'enable_http',
        'verify',
        'enable_http2',
        'max_connections',
        'max_keepalive_connections',
        'keepalive_expiry',
        'local_addresses',
        'proxies',
        'using_tor_proxy',
        'max_redirects',
        'retries',
        'retry_on_http_error',
        '_local_addresses_cycle',
        '_proxies_cycle',
        '_clients',
        '_logger',
    )

    _TOR_CHECK_RESULT = {}

    def __init__(
        # pylint: disable=too-many-arguments
        self,
        enable_http=True,
        verify=True,
        enable_http2=False,
        max_connections=None,
        max_keepalive_connections=None,
        keepalive_expiry=None,
        proxies=None,
        using_tor_proxy=False,
        local_addresses=None,
        retries=0,
        retry_on_http_error=None,
        max_redirects=30,
        logger_name=None,
    ):

        self.enable_http = enable_http
        self.verify = verify
        self.enable_http2 = enable_http2
        self.max_connections = max_connections
        self.max_keepalive_connections = max_keepalive_connections
        self.keepalive_expiry = keepalive_expiry
        self.proxies = proxies
        self.using_tor_proxy = using_tor_proxy
        self.local_addresses = local_addresses
        self.retries = retries
        self.retry_on_http_error = retry_on_http_error
        self.max_redirects = max_redirects
        self._local_addresses_cycle = self.get_ipaddress_cycle()
        self._proxies_cycle = self.get_proxy_cycles()
        self._clients = {}
        self._logger = logger.getChild(logger_name) if logger_name else logger
        self.check_parameters()

    def check_parameters(self):
        for address in self.iter_ipaddresses():
            if '/' in address:
                ipaddress.ip_network(address, False)
            else:
                ipaddress.ip_address(address)

        if self.proxies is not None and not isinstance(self.proxies, (str, dict)):
            raise ValueError('proxies type has to be str, dict or None')

    def iter_ipaddresses(self):
        local_addresses = self.local_addresses
        if not local_addresses:
            return
        if isinstance(local_addresses, str):
            local_addresses = [local_addresses]
        for address in local_addresses:
            yield address

    def get_ipaddress_cycle(self):
        while True:
            count = 0
            for address in self.iter_ipaddresses():
                if '/' in address:
                    for a in ipaddress.ip_network(address, False).hosts():
                        yield str(a)
                        count += 1
                else:
                    a = ipaddress.ip_address(address)
                    yield str(a)
                    count += 1
            if count == 0:
                yield None

    def iter_proxies(self):
        if not self.proxies:
            return
        # https://www.python-httpx.org/compatibility/#proxy-keys
        if isinstance(self.proxies, str):
            yield 'all://', [self.proxies]
        else:
            for pattern, proxy_url in self.proxies.items():
                pattern = PROXY_PATTERN_MAPPING.get(pattern, pattern)
                if isinstance(proxy_url, str):
                    proxy_url = [proxy_url]
                yield pattern, proxy_url

    def get_proxy_cycles(self):
        proxy_settings = {}
        for pattern, proxy_urls in self.iter_proxies():
            proxy_settings[pattern] = cycle(proxy_urls)
        while True:
            # pylint: disable=stop-iteration-return
            yield tuple((pattern, next(proxy_url_cycle)) for pattern, proxy_url_cycle in proxy_settings.items())

    async def log_response(self, response: httpx.Response):
        request = response.request
        status = f"{response.status_code} {response.reason_phrase}"
        response_line = f"{response.http_version} {status}"
        content_type = response.headers.get("Content-Type")
        content_type = f' ({content_type})' if content_type else ''
        self._logger.debug(f'HTTP Request: {request.method} {request.url} "{response_line}"{content_type}')

    @staticmethod
    async def check_tor_proxy(client: httpx.AsyncClient, proxies) -> bool:
        if proxies in Network._TOR_CHECK_RESULT:
            return Network._TOR_CHECK_RESULT[proxies]

        result = True
        # ignore client._transport because it is not used with all://
        for transport in client._mounts.values():  # pylint: disable=protected-access
            if isinstance(transport, AsyncHTTPTransportNoHttp):
                continue
            if getattr(transport, "_pool") and getattr(
                transport._pool, "_rdns", False  # pylint: disable=protected-access
            ):
                continue
            return False
        response = await client.get("https://check.torproject.org/api/ip", timeout=10)
        if not response.json()["IsTor"]:
            result = False
        Network._TOR_CHECK_RESULT[proxies] = result
        return result

    async def get_client(self, verify=None, max_redirects=None):
        verify = self.verify if verify is None else verify
        max_redirects = self.max_redirects if max_redirects is None else max_redirects
        local_address = next(self._local_addresses_cycle)
        proxies = next(self._proxies_cycle)  # is a tuple so it can be part of the key
        key = (verify, max_redirects, local_address, proxies)
        hook_log_response = self.log_response if searx_debug else None
        if key not in self._clients or self._clients[key].is_closed:
            client = new_client(
                self.enable_http,
                verify,
                self.enable_http2,
                self.max_connections,
                self.max_keepalive_connections,
                self.keepalive_expiry,
                dict(proxies),
                local_address,
                0,
                max_redirects,
                hook_log_response,
            )
            if self.using_tor_proxy and not await self.check_tor_proxy(client, proxies):
                await client.aclose()
                raise httpx.ProxyError('Network configuration problem: not using Tor')
            self._clients[key] = client
        return self._clients[key]

    async def aclose(self):
        async def close_client(client):
            try:
                await client.aclose()
            except httpx.HTTPError:
                pass

        await asyncio.gather(*[close_client(client) for client in self._clients.values()], return_exceptions=False)

    @staticmethod
    def extract_kwargs_clients(kwargs):
        kwargs_clients = {}
        if 'verify' in kwargs:
            kwargs_clients['verify'] = kwargs.pop('verify')
        if 'max_redirects' in kwargs:
            kwargs_clients['max_redirects'] = kwargs.pop('max_redirects')
        if 'allow_redirects' in kwargs:
            # see https://github.com/encode/httpx/pull/1808
            kwargs['follow_redirects'] = kwargs.pop('allow_redirects')
        return kwargs_clients

    def is_valid_response(self, response):
        # pylint: disable=too-many-boolean-expressions
        if (
            (self.retry_on_http_error is True and 400 <= response.status_code <= 599)
            or (isinstance(self.retry_on_http_error, list) and response.status_code in self.retry_on_http_error)
            or (isinstance(self.retry_on_http_error, int) and response.status_code == self.retry_on_http_error)
        ):
            return False
        return True

    async def call_client(self, stream, method, url, **kwargs):
        retries = self.retries
        was_disconnected = False
        kwargs_clients = Network.extract_kwargs_clients(kwargs)
        while retries >= 0:  # pragma: no cover
            client = await self.get_client(**kwargs_clients)
            try:
                if stream:
                    response = client.stream(method, url, **kwargs)
                else:
                    response = await client.request(method, url, **kwargs)
                if self.is_valid_response(response) or retries <= 0:
                    return response
            except httpx.RemoteProtocolError as e:
                if not was_disconnected:
                    # the server has closed the connection:
                    # try again without decreasing the retries variable & with a new HTTP client
                    was_disconnected = True
                    await client.aclose()
                    self._logger.warning('httpx.RemoteProtocolError: the server has disconnected, retrying')
                    continue
                if retries <= 0:
                    raise e
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                if retries <= 0:
                    raise e
            retries -= 1

    async def request(self, method, url, **kwargs):
        return await self.call_client(False, method, url, **kwargs)

    async def stream(self, method, url, **kwargs):
        return await self.call_client(True, method, url, **kwargs)

    @classmethod
    async def aclose_all(cls):
        await asyncio.gather(*[network.aclose() for network in NETWORKS.values()], return_exceptions=False)


def get_network(name=None):
    return NETWORKS.get(name or DEFAULT_NAME)


def check_network_configuration():
    async def check():
        exception_count = 0
        for network in NETWORKS.values():
            if network.using_tor_proxy:
                try:
                    await network.get_client()
                except Exception:  # pylint: disable=broad-except
                    network._logger.exception('Error')  # pylint: disable=protected-access
                    exception_count += 1
        return exception_count

    future = asyncio.run_coroutine_threadsafe(check(), get_loop())
    exception_count = future.result()
    if exception_count > 0:
        raise RuntimeError("Invalid network configuration")


def initialize(settings_engines=None, settings_outgoing=None):
    # pylint: disable=import-outside-toplevel)
    from searx.engines import engines
    from searx import settings

    # pylint: enable=import-outside-toplevel)

    settings_engines = settings_engines or settings['engines']
    settings_outgoing = settings_outgoing or settings['outgoing']

    # default parameters for AsyncHTTPTransport
    # see https://github.com/encode/httpx/blob/e05a5372eb6172287458b37447c30f650047e1b8/httpx/_transports/default.py#L108-L121  # pylint: disable=line-too-long
    default_params = {
        'enable_http': False,
        'verify': True,
        'enable_http2': settings_outgoing['enable_http2'],
        'max_connections': settings_outgoing['pool_connections'],
        'max_keepalive_connections': settings_outgoing['pool_maxsize'],
        'keepalive_expiry': settings_outgoing['keepalive_expiry'],
        'local_addresses': settings_outgoing['source_ips'],
        'using_tor_proxy': settings_outgoing['using_tor_proxy'],
        'proxies': settings_outgoing['proxies'],
        'max_redirects': settings_outgoing['max_redirects'],
        'retries': settings_outgoing['retries'],
        'retry_on_http_error': None,
    }

    def new_network(params, logger_name=None):
        nonlocal default_params
        result = {}
        result.update(default_params)
        result.update(params)
        if logger_name:
            result['logger_name'] = logger_name
        return Network(**result)

    def iter_networks():
        nonlocal settings_engines
        for engine_spec in settings_engines:
            engine_name = engine_spec['name']
            engine = engines.get(engine_name)
            if engine is None:
                continue
            network = getattr(engine, 'network', None)
            yield engine_name, engine, network

    if NETWORKS:
        done()
    NETWORKS.clear()
    NETWORKS[DEFAULT_NAME] = new_network({}, logger_name='default')
    NETWORKS['ipv4'] = new_network({'local_addresses': '0.0.0.0'}, logger_name='ipv4')
    NETWORKS['ipv6'] = new_network({'local_addresses': '::'}, logger_name='ipv6')

    # define networks from outgoing.networks
    for network_name, network in settings_outgoing['networks'].items():
        NETWORKS[network_name] = new_network(network, logger_name=network_name)

    # define networks from engines.[i].network (except references)
    for engine_name, engine, network in iter_networks():
        if network is None:
            network = {}
            for attribute_name, attribute_value in default_params.items():
                if hasattr(engine, attribute_name):
                    network[attribute_name] = getattr(engine, attribute_name)
                else:
                    network[attribute_name] = attribute_value
            NETWORKS[engine_name] = new_network(network, logger_name=engine_name)
        elif isinstance(network, dict):
            NETWORKS[engine_name] = new_network(network, logger_name=engine_name)

    # define networks from engines.[i].network (references)
    for engine_name, engine, network in iter_networks():
        if isinstance(network, str):
            NETWORKS[engine_name] = NETWORKS[network]

    # the /image_proxy endpoint has a dedicated network.
    # same parameters than the default network, but HTTP/2 is disabled.
    # It decreases the CPU load average, and the total time is more or less the same
    if 'image_proxy' not in NETWORKS:
        image_proxy_params = default_params.copy()
        image_proxy_params['enable_http2'] = False
        NETWORKS['image_proxy'] = new_network(image_proxy_params, logger_name='image_proxy')


@atexit.register
def done():
    """Close all HTTP client

    Avoid a warning at exit
    see https://github.com/encode/httpx/blob/1a6e254f72d9fd5694a1c10a28927e193ab4f76b/httpx/_client.py#L1785

    Note: since Network.aclose has to be async, it is not possible to call this method on Network.__del__
    So Network.aclose is called here using atexit.register
    """
    try:
        loop = get_loop()
        if loop:
            future = asyncio.run_coroutine_threadsafe(Network.aclose_all(), loop)
            # wait 3 seconds to close the HTTP clients
            future.result(3)
    finally:
        NETWORKS.clear()


NETWORKS[DEFAULT_NAME] = Network()
