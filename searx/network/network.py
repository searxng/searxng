# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=global-statement
# pylint: disable=missing-module-docstring, missing-class-docstring
"""Deal with 

* create Networks from settings.yml
* each Network contains an ABCHTTPClient for each (proxies, IP addresses). Lazy initialized.
* a Network provides two methods:

  * get_http_client: returns an HTTP client. Prefer the get_context,
    retry strategy is ignored with get_http_client
  * get_context: provides a runtime context for the engine, see searx.network.context
"""

import ipaddress
from dataclasses import dataclass, field
from enum import Enum
from itertools import cycle
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union

import httpx

from searx import logger, searx_debug
from searx.network.client import HTTPClient, TorHTTPClient
from searx.network.context import (
    NetworkContext,
    NetworkContextRetryDifferentHTTPClient,
    NetworkContextRetryFunction,
    NetworkContextRetrySameHTTPClient,
)

logger = logger.getChild('network')


class RetryStrategy(Enum):
    ENGINE = NetworkContextRetryFunction
    SAME_HTTP_CLIENT = NetworkContextRetrySameHTTPClient
    DIFFERENT_HTTP_CLIENT = NetworkContextRetryDifferentHTTPClient


TYPE_IP_ANY = Union[  # pylint: disable=invalid-name
    ipaddress.IPv4Address,
    ipaddress.IPv6Address,
    ipaddress.IPv4Network,
    ipaddress.IPv6Network,
]

TYPE_RETRY_ON_ERROR = Union[List[int], int, bool]  # pylint: disable=invalid-name


@dataclass(order=True, frozen=True)
class NetworkSettings:
    """Configuration for a Network. See NetworkSettingsReader

    TODO: check if we need order=True
    """

    # Individual HTTP requests can override these parameters.
    verify: bool = True
    max_redirects: int = 30
    # These parameters can not be overridden.
    enable_http: bool = False  # disable http:// URL (unencrypted) by default = make sure to use HTTPS
    enable_http2: bool = True
    max_connections: Optional[int] = 10
    max_keepalive_connections: Optional[int] = 100
    keepalive_expiry: Optional[float] = 5.0
    local_addresses: List[TYPE_IP_ANY] = field(default_factory=list)
    proxies: Dict[str, List[str]] = field(default_factory=dict)
    using_tor_proxy: bool = False
    retries: int = 0
    retry_strategy: RetryStrategy = RetryStrategy.DIFFERENT_HTTP_CLIENT
    retry_on_http_error: Optional[TYPE_RETRY_ON_ERROR] = None
    logger_name: Optional[str] = None


class Network:
    """Provides NetworkContext and ABCHTTPClient following NetworkSettings.

    A Network might have multiple IP addresses and proxies;
    in this case, each call to get_context or get_http_client provides a different
    configuration.
    """

    __slots__ = (
        '_settings',
        '_local_addresses_cycle',
        '_proxies_cycle',
        '_clients',
        '_logger',
    )

    def __init__(self, settings: NetworkSettings):
        """Creates a Network from a NetworkSettings"""
        self._settings = settings
        self._local_addresses_cycle = self._get_local_addresses_cycle()
        self._proxies_cycle = self._get_proxy_cycles()
        self._clients: Dict[Tuple, HTTPClient] = {}
        self._logger = logger.getChild(settings.logger_name) if settings.logger_name else logger

    @staticmethod
    def from_dict(**kwargs):
        """Creates a Network from a keys/values"""
        return Network(NetwortSettingsDecoder.from_dict(kwargs))

    def close(self):
        """Close all the ABCHTTPClient hold by the Network"""
        for client in self._clients.values():
            client.close()

    def check_configuration(self) -> bool:
        """Check if the network configuration is valid.

        Typical use case: check if the proxy is really a Tor proxy"""
        try:
            self._get_http_client()
            return True
        except Exception:  # pylint: disable=broad-except
            self._logger.exception('Error')
            return False

    def get_context(self, timeout: Optional[float] = None, start_time: Optional[float] = None) -> NetworkContext:
        """Return a new NetworkContext"""
        context_cls = self._settings.retry_strategy.value
        return context_cls(self._settings.retries, self._get_http_client, start_time, timeout)

    def _get_http_client(self) -> HTTPClient:
        """Return an HTTP client.

        Different HTTP clients are returned according to the configuration.

        For example, if two proxies are defined,
        the first call to this function returns an HTTP client using the first proxy.
        A second call returns an HTTP client using the second proxy.
        A third call returns the same HTTP client from the first call, using the first proxy.
        """
        local_addresses = next(self._local_addresses_cycle)
        proxies = next(self._proxies_cycle)  # is a tuple so it can be part of the key
        key = (local_addresses, proxies)
        if key not in self._clients or self._clients[key].is_closed:
            http_client_cls = TorHTTPClient if self._settings.using_tor_proxy else HTTPClient
            hook_log_response = self._log_response if searx_debug else None
            log_trace = self._log_trace if searx_debug else None
            self._clients[key] = http_client_cls(
                verify=self._settings.verify,
                enable_http=self._settings.enable_http,
                enable_http2=self._settings.enable_http2,
                max_connections=self._settings.max_connections,
                max_keepalive_connections=self._settings.max_keepalive_connections,
                keepalive_expiry=self._settings.keepalive_expiry,
                proxies=dict(proxies),
                local_addresses=local_addresses,
                retry_on_http_error=self._settings.retry_on_http_error,
                hook_log_response=hook_log_response,
                log_trace=log_trace,
                logger=self._logger,
            )
        return self._clients[key]

    def _get_local_addresses_cycle(self):
        """Never-ending generator of IP addresses"""
        while True:
            at_least_one = False
            for address in self._settings.local_addresses:
                if isinstance(address, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
                    for a in address.hosts():
                        yield str(a)
                        at_least_one = True
                else:
                    yield str(address)
                    at_least_one = True
            if not at_least_one:
                # IPv4Network.hosts() and IPv6Network.hosts() might never return an IP address.
                # at_least_one makes sure the generator does not turn into infinite loop without yield
                yield None

    def _get_proxy_cycles(self):
        """Never-ending generator of proxy configurations.

        Each iteration returns tuples of tuples.
        Semantically, this is a dictionary where
        * keys are the mount points (see https://www.python-httpx.org/advanced/#mounting-transports )
        * values are the proxy URLs.

        This private method returns a tuple instead of a dictionary to be hashable.
        See the line `key = (local_addresses, proxies)` above.

        For example, if settings.yml contains:
        ```yaml
        proxies: socks5h://localhost:1337
        ```

        This is equivalent to
        ```yaml
        proxies:
            - all://: socks5h://localhost:1337
        ```

        And this method always returns:
        * `(('all://', 'socks5h://localhost:1337'))`

        Another example:

        ```yaml
        proxies:
            - all://: socks5h://localhost:1337
            - https://bing.com:
                    - socks5h://localhost:4000
                    - socks5h://localhost:5000
        ```

        In this example, this method alternately returns these two responses:

        * `(('all://', 'socks5h://localhost:1337'), ('https://bing.com', 'socks5h://localhost:4000'))`
        * `(('all://', 'socks5h://localhost:1337'), ('https://bing.com', 'socks5h://localhost:5000'))`

        When no proxies are configured, this method returns an empty tuple at each iteration.
        """
        # for each pattern, turn each list of proxy into a cycle
        proxy_settings = {pattern: cycle(proxy_urls) for pattern, proxy_urls in (self._settings.proxies).items()}
        while True:
            # pylint: disable=stop-iteration-return
            # ^^ is it a pylint bug ?
            yield tuple((pattern, next(proxy_url_cycle)) for pattern, proxy_url_cycle in proxy_settings.items())

    def _log_response(self, response: httpx.Response):
        """Logs from httpx are disabled. Log the HTTP response with the logger from the network"""
        request = response.request
        status = f"{response.status_code} {response.reason_phrase}"
        response_line = f"{response.http_version} {status}"
        content_type = response.headers.get("Content-Type")
        content_type = f' ({content_type})' if content_type else ''
        self._logger.debug(f'HTTP Request: {request.method} {request.url} "{response_line}"{content_type}')

    def _log_trace(self, name: str, info: Mapping[str, Any]) -> None:
        """Log the actual source / dest IPs and SSL cipher.

        Note: does not work with socks proxy

        See
        * https://www.encode.io/httpcore/extensions/
        * https://github.com/encode/httpx/blob/e874351f04471029b2c5dcb2d0b50baccc7b9bc0/httpx/_main.py#L207
        """
        if name == "connection.connect_tcp.complete":
            stream = info["return_value"]
            server_addr = stream.get_extra_info("server_addr")
            client_addr = stream.get_extra_info("client_addr")
            self._logger.debug(f"* Connected from {client_addr[0]!r} to {server_addr[0]!r} on port {server_addr[1]}")
        elif name == "connection.start_tls.complete":  # pragma: no cover
            stream = info["return_value"]
            ssl_object = stream.get_extra_info("ssl_object")
            version = ssl_object.version()
            cipher = ssl_object.cipher()
            alpn = ssl_object.selected_alpn_protocol()
            self._logger.debug(f"* SSL established using {version!r} / {cipher[0]!r}, ALPN protocol: {alpn!r}")
        elif name == "http2.send_request_headers.started":
            self._logger.debug(f"* HTTP/2 stream_id: {info['stream_id']}")

    def __repr__(self):
        return f"<{self.__class__.__name__} logger_name={self._settings.logger_name!r}>"


class NetwortSettingsDecoder:
    """Convert a description of a network in settings.yml to a NetworkSettings instance"""

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

    @classmethod
    def from_dict(cls, network_settings: Dict[str, Any]) -> NetworkSettings:
        # Decode the parameters that require it; the other parameters are left as they are
        decoders = {
            "proxies": cls._decode_proxies,
            "local_addresses": cls._decode_local_addresses,
            "retry_strategy": cls._decode_retry_strategy,
        }
        for key, decode_func in decoders.items():
            if key not in network_settings:
                continue
            if network_settings[key] is None:
                # None is seen as not set: rely on the default values from NetworkSettings
                del network_settings[key]
            else:
                network_settings[key] = decode_func(network_settings[key])
        # Relies on the default values of NetworkSettings for unset parameters
        return NetworkSettings(**network_settings)

    @classmethod
    def _decode_proxies(cls, proxies) -> Dict[str, List[str]]:
        if isinstance(proxies, str):
            # for example:
            # proxies: socks5://localhost:8000
            proxies = {'all://': [proxies]}
        elif isinstance(proxies, list):
            # for example:
            # proxies:
            #   - socks5h://localhost:8000
            #   - socks5h://localhost:8001
            proxies = {'all://': proxies}

        if not isinstance(proxies, dict):
            raise ValueError('proxies type has to be str, list, dict or None')

        # Here we are sure to have
        # proxies = {
        #   pattern: a_value
        # }
        # with a_value that can be either a string or a list.
        # Now, we make sure that a_value is always a list of strings.
        # Also, we keep compatibility with requests regarding the patterns:
        # see https://www.python-httpx.org/compatibility/#proxy-keys
        result = {}
        for pattern, proxy_list in proxies.items():
            pattern = cls.PROXY_PATTERN_MAPPING.get(pattern, pattern)
            if isinstance(proxy_list, str):
                proxy_list = [proxy_list]
            if not isinstance(proxy_list, list):
                raise ValueError('proxy list')
            for proxy in proxy_list:
                if not isinstance(proxy, str):
                    raise ValueError(f'{repr(proxy)} : an URL is expected')
            result[pattern] = proxy_list
        return result

    @staticmethod
    def _decode_local_addresses(ip_addresses: Union[str, List[str]]) -> List[TYPE_IP_ANY]:
        if isinstance(ip_addresses, str):
            ip_addresses = [ip_addresses]

        if not isinstance(ip_addresses, list):
            raise ValueError('IP address must be either None or a string or a list of strings')

        # check IP address syntax
        result = []
        for address in ip_addresses:
            if not isinstance(address, str):
                raise ValueError(f'An {address!r} must be an IP address written as a string')
            if '/' in address:
                result.append(ipaddress.ip_network(address, False))
            else:
                result.append(ipaddress.ip_address(address))
        return result

    @staticmethod
    def _decode_retry_strategy(retry_strategy: str) -> RetryStrategy:
        for member in RetryStrategy:
            if member.name.lower() == retry_strategy.lower():
                return member
        raise ValueError(f"{retry_strategy} is not a RetryStrategy")


class NetworkManager:
    """Contains all the Network instances.

    By default, there is one default network with the default parameters,
    so @searx.network.provide_networkcontext() works out of the box.
    """

    DEFAULT_NAME = '__DEFAULT__'

    def __init__(self):
        # Create a default network so scripts in searxng_extra don't have load settings.yml
        self.networks: Dict[str, Network] = {NetworkManager.DEFAULT_NAME: Network.from_dict()}

    def get(self, name: Optional[str] = None):
        return self.networks[name or NetworkManager.DEFAULT_NAME]

    def initialize_from_settings(self, settings_engines, settings_outgoing, check=True):
        # pylint: disable=too-many-branches
        from searx.engines import engines  # pylint: disable=import-outside-toplevel

        # Default parameters for HTTPTransport
        # see https://github.com/encode/httpx/blob/e05a5372eb6172287458b37447c30f650047e1b8/httpx/_transports/default.py#L108-L121  # pylint: disable=line-too-long
        default_network_settings = {
            'verify': settings_outgoing['verify'],
            'enable_http': settings_outgoing['enable_http'],
            'enable_http2': settings_outgoing['enable_http2'],
            'max_connections': settings_outgoing['pool_connections'],  # different because of historical reason
            'max_keepalive_connections': settings_outgoing['pool_maxsize'],  # different because of historical reason
            'keepalive_expiry': settings_outgoing['keepalive_expiry'],
            'max_redirects': settings_outgoing['max_redirects'],
            'retries': settings_outgoing['retries'],
            'proxies': settings_outgoing['proxies'],
            'local_addresses': settings_outgoing['source_ips'],  # different because of historical reason
            'using_tor_proxy': settings_outgoing['using_tor_proxy'],
            'retry_on_http_error': None,
        }

        def new_network(network_settings: Dict[str, Any], logger_name: Optional[str] = None):
            nonlocal default_network_settings
            result = {}
            result.update(default_network_settings)
            result.update(network_settings)
            if logger_name:
                result['logger_name'] = logger_name
            return Network.from_dict(**result)

        # ipv4 and ipv6 are always defined
        self.networks = {
            NetworkManager.DEFAULT_NAME: new_network({}, logger_name='default'),
            'ipv4': new_network({'local_addresses': '0.0.0.0'}, logger_name='ipv4'),
            'ipv6': new_network({'local_addresses': '::'}, logger_name='ipv6'),
        }

        # define networks from outgoing.networks. Example of configuration:
        #
        # outgoing:
        #   networks:
        #     my_proxy:
        #       proxies: http://localhost:1337
        #
        for network_name, network_dict in settings_outgoing['networks'].items():
            self.networks[network_name] = new_network(network_dict, logger_name=network_name)

        # Get the engine network settings directly from the engine modules and settings.yml (not as NetworkSettings)
        engine_network_dict_settings = {}
        for engine_spec in settings_engines:
            engine_name = engine_spec['name']
            engine = engines.get(engine_name)
            if engine is None:
                continue
            engine_network_dict_settings[engine_name] = self._get_engine_network_settings(
                engine_name, engine, default_network_settings
            )

        # Define networks from engines.[i].network (except references)
        for engine_name, network_dict in engine_network_dict_settings.items():
            if isinstance(network_dict, dict):
                self.networks[engine_name] = new_network(network_dict, logger_name=engine_name)

        # Define networks from engines.[i].network (only references)
        for engine_name, network_dict in engine_network_dict_settings.items():
            if isinstance(network_dict, str):
                self.networks[engine_name] = self.networks[network_dict]

        # The /image_proxy endpoint has a dedicated network using the same parameters
        # as the default network, but HTTP/2 is disabled. It decreases the CPU load average,
        # and the total time is more or less the same.
        if 'image_proxy' not in self.networks:
            image_proxy_params = default_network_settings.copy()
            image_proxy_params['enable_http2'] = False
            self.networks['image_proxy'] = new_network(image_proxy_params, logger_name='image_proxy')

        # Define a network the autocompletion
        if 'autocomplete' not in self.networks:
            self.networks['autocomplete'] = new_network(default_network_settings, logger_name='autocomplete')

        # Check if each network is valid:
        # * one HTTP client is instantiated
        #   --> Tor connectivity is checked if using_tor_proxy is True
        if check:
            exception_count = 0
            for network in self.networks.values():
                if not network.check_configuration():
                    exception_count += 1
            if exception_count > 0:
                raise RuntimeError("Invalid network configuration")

    @staticmethod
    def _get_engine_network_settings(engine_name, engine, default_network_settings):
        if hasattr(engine, 'network'):
            # The network configuration is defined in settings.yml inside a network key.
            # For example:
            #
            #  - name: arxiv
            #    engine: arxiv
            #    shortcut: arx
            #    network:
            #      http2: false
            #      proxies: socks5h://localhost:1337
            #
            network = getattr(engine, 'network', None)
            if not isinstance(network, (dict, str)):
                raise ValueError(f'Engine {engine_name}: network must be a dictionnary or string')
            return network
        # The network settings are mixed with the other engine settings.
        # The code checks if the keys from default_network_settings are defined in the engine module
        #
        # For example:
        #
        #  - name: arxiv
        #    engine: arxiv
        #    shortcut: arx
        #    http2: false
        #    proxies: socks5h://localhost:1337
        #
        return {
            attribute_name: getattr(engine, attribute_name)
            for attribute_name in default_network_settings.keys()
            if hasattr(engine, attribute_name)
        }


NETWORKS = NetworkManager()
