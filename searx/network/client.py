# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring, global-statement
"""Implement various ABCHTTPClient

* OneHTTPClient        wrapper around httpx.Client
* BaseHTTPClient       httpx.Client accept the verify and max_redirects parameter only in the constructor.
                       BaseHTTPClient allows to pass these parameter in each query by creating multiple OneHTTPClient.
* HTTPClient           Inherit from BaseHTTPClient, raise an error according to retry_on_http_error parameter.
* TorHTTPClient        Inherit from HTTPClientSoftError, check Tor connectivity
"""

import random
from abc import ABC, abstractmethod
from collections import namedtuple
from ssl import SSLContext
from typing import Any, Dict, Optional, Tuple, Union

import httpx
from httpx_socks import SyncProxyTransport
from python_socks import ProxyConnectionError, ProxyError, ProxyTimeoutError, parse_proxy_url

from .raise_for_httperror import raise_for_httperror

CertTypes = Union[
    # certfile
    str,
    # (certfile, keyfile)
    Tuple[str, Optional[str]],
    # (certfile, keyfile, password)
    Tuple[str, Optional[str], Optional[str]],
]

SSLCONTEXTS: Dict[Any, SSLContext] = {}


class _NotSetClass:  # pylint: disable=too-few-public-methods
    """Internal class for this module, do not create instance of this class.
    Replace the None value, allow explicitly pass None as a function argument"""


NOTSET = _NotSetClass()


class SoftRetryHTTPException(Exception):
    """Client implementations raise this exception to tell the NetworkContext
    the response is invalid even if there is no HTTP exception.

    This exception is INTERNAL to searx.network and must not be seen outside.

    See HTTPClientSoftError which check the HTTP response according to
    the raise_for_httperror parameter.
    """

    def __init__(self, response):
        self.response = response
        message = "SoftRetryHTTPException, you should not see this error"
        super().__init__(message)


def _shuffle_ciphers(ssl_context):
    """Shuffle httpx's default ciphers of a SSL context randomly.

    From `What Is TLS Fingerprint and How to Bypass It`_

    > When implementing TLS fingerprinting, servers can't operate based on a
    > locked-in whitelist database of fingerprints.  New fingerprints appear
    > when web clients or TLS libraries release new versions. So, they have to
    > live off a blocklist database instead.
    > ...
    > It's safe to leave the first three as is but shuffle the remaining ciphers
    > and you can bypass the TLS fingerprint check.

    .. _What Is TLS Fingerprint and How to Bypass It:
       https://www.zenrows.com/blog/what-is-tls-fingerprint#how-to-bypass-tls-fingerprinting

    """
    c_list = httpx._config.DEFAULT_CIPHERS.split(':')  # pylint: disable=protected-access
    sc_list, c_list = c_list[:3], c_list[3:]
    random.shuffle(c_list)
    ssl_context.set_ciphers(":".join(sc_list + c_list))


def _get_sslcontexts(
    local_address: str,
    proxy_url: Optional[str],
    cert: Optional[CertTypes],
    verify: Union[str, bool],
    trust_env: bool,
    http2: bool,
):
    key = (local_address, proxy_url, cert, verify, trust_env, http2)
    if key not in SSLCONTEXTS:
        SSLCONTEXTS[key] = httpx.create_ssl_context(cert, verify, trust_env, http2)
    _shuffle_ciphers(SSLCONTEXTS[key])
    return SSLCONTEXTS[key]


### Transport


class _HTTPTransportNoHttp(httpx.HTTPTransport):
    """Block HTTP request

    The constructor is blank because httpx.HTTPTransport.__init__ creates an SSLContext unconditionally:
    https://github.com/encode/httpx/blob/0f61aa58d66680c239ce43c8cdd453e7dc532bfc/httpx/_transports/default.py#L271

    Each SSLContext consumes more than 500kb of memory, since there is about one network per engine.

    In consequence, this class overrides all public methods

    For reference: https://github.com/encode/httpx/issues/2298
    """

    def __init__(self, *args, **kwargs):
        # pylint: disable=super-init-not-called
        # this on purpose if the base class is not called
        pass

    def handle_request(self, request):
        raise httpx.UnsupportedProtocol('HTTP protocol is disabled')

    def close(self) -> None:
        pass

    def __enter__(self):  # Use generics for subclass support.
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # pylint: disable=signature-differs
        # avoid to import the various type for the signature, but pylint is not happy
        pass


class _CustomSyncProxyTransport(SyncProxyTransport):
    """Inherit from httpx_socks.SyncProxyTransport

    Map python_socks exceptions to httpx.ProxyError exceptions
    """

    def handle_request(self, request):
        try:
            return super().handle_request(request)
        except ProxyConnectionError as e:
            raise httpx.ProxyError("ProxyConnectionError: " + e.strerror, request=request) from e
        except ProxyTimeoutError as e:
            raise httpx.ProxyError("ProxyTimeoutError: " + e.args[0], request=request) from e
        except ProxyError as e:
            raise httpx.ProxyError("ProxyError: " + e.args[0], request=request) from e


def _get_transport_for_socks_proxy(verify, http2, local_address, proxy_url, limit, retries):
    # support socks5h (requests compatibility):
    # https://requests.readthedocs.io/en/master/user/advanced/#socks
    # socks5://   hostname is resolved on client side
    # socks5h://  hostname is resolved on proxy side
    rdns = False
    socks5h = 'socks5h://'
    if proxy_url.startswith(socks5h):
        proxy_url = 'socks5://' + proxy_url[len(socks5h) :]
        rdns = True

    proxy_type, proxy_host, proxy_port, proxy_username, proxy_password = parse_proxy_url(proxy_url)
    verify = _get_sslcontexts(local_address, proxy_url, None, verify, True, http2) if verify is True else verify

    # About verify: in ProxyTransportFixed, verify is of type httpx._types.VerifyTypes
    return _CustomSyncProxyTransport(
        proxy_type=proxy_type,
        proxy_host=proxy_host,
        proxy_port=proxy_port,
        username=proxy_username,
        password=proxy_password,
        rdns=rdns,
        verify=verify,  # type: ignore
        http2=http2,
        local_address=local_address,
        limits=limit,
        retries=retries,
    )


def _get_transport(verify, http2, local_address, proxy_url, limit, retries):
    verify = _get_sslcontexts(local_address, None, None, verify, True, http2) if verify is True else verify
    return httpx.HTTPTransport(
        # pylint: disable=protected-access
        verify=verify,
        http2=http2,
        limits=limit,
        proxy=httpx._config.Proxy(proxy_url) if proxy_url else None,
        local_address=local_address,
        retries=retries,
    )


### Clients


class ABCHTTPClient(ABC):
    """Abstract HTTP client

    Multiple implementation are defined bellow.
    There are like an onion: each implementation relies on the previous one
    and bring new feature.
    """

    @abstractmethod
    def send(self, stream: bool, method: str, url: str, **kwargs) -> httpx.Response:
        pass

    @abstractmethod
    def close(self):
        pass

    @property
    @abstractmethod
    def is_closed(self) -> bool:
        pass

    def request(self, method, url, **kwargs) -> httpx.Response:
        return self.send(False, method, url, **kwargs)

    def stream(self, method, url, **kwargs) -> httpx.Response:
        return self.send(True, method, url, **kwargs)


class OneHTTPClient(ABCHTTPClient):
    """Wrap a httpx.Client

    Use httpx_socks for socks proxies.

    Deal with httpx.RemoteProtocolError exception: httpx raises this exception when the
    HTTP/2 server disconnect. It is excepted to reconnect.
    Related to https://github.com/encode/httpx/issues/1478
    Perhaps it can be removed now : TODO check in production.

    To be backward compatible with Request:

        * In Response, "ok" is set to "not response.is_error()"
          See https://www.python-httpx.org/compatibility/#checking-for-success-and-failure-responses

        * allow_redirects is accepted
          See https://www.python-httpx.org/compatibility/#redirects
    """

    def __init__(
        # pylint: disable=too-many-arguments
        self,
        verify=True,
        enable_http=True,
        enable_http2=False,
        max_connections=None,
        max_keepalive_connections=None,
        keepalive_expiry=None,
        proxies=None,
        local_addresses=None,
        max_redirects=30,
        hook_log_response=None,
        log_trace=None,
        allow_redirects=True,
        logger=None,
    ):
        self.enable_http = enable_http
        self.verify = verify
        self.enable_http2 = enable_http2
        self.max_connections = max_connections
        self.max_keepalive_connections = max_keepalive_connections
        self.keepalive_expiry = keepalive_expiry
        self.proxies = proxies or {}
        self.local_address = local_addresses
        self.max_redirects = max_redirects
        self.hook_log_response = hook_log_response
        self.allow_redirects = allow_redirects
        self.logger = logger
        self.extensions = None
        if log_trace:
            self.extensions = {"trace": log_trace}
        self._new_client()

    def send(self, stream, method, url, timeout=None, **kwargs):
        self._patch_request(kwargs)
        retry = 1
        response = None
        while retry >= 0:  # pragma: no cover
            retry -= 1
            try:
                if stream:
                    # from https://www.python-httpx.org/async/#streaming-responses
                    # > For situations when context block usage is not practical,
                    # > it is possible to enter "manual mode" by sending a Request
                    # > instance using client.send(..., stream=True).
                    request = self.client.build_request(
                        method=method,
                        url=url,
                        content=kwargs.get("content"),
                        data=kwargs.get("data"),
                        files=kwargs.get("files"),
                        json=kwargs.get("json"),
                        params=kwargs.get("params"),
                        headers=kwargs.get("headers"),
                        cookies=kwargs.get("cookies"),
                        timeout=timeout,
                        extensions=self.extensions,
                    )
                    response = self.client.send(
                        request,
                        stream=True,
                        follow_redirects=kwargs.get("follow_redirects", False),
                        auth=kwargs.get("auth"),
                    )
                else:
                    response = self.client.request(method, url, extensions=self.extensions, timeout=timeout, **kwargs)
                self._patch_response(response)
                return response
            except httpx.RemoteProtocolError as e:
                if response:
                    response.close()
                if retry >= 0:
                    # the server has closed the connection:
                    # try again without decreasing the retries variable & with a new HTTP client
                    self._reconnect_client()
                    if self.logger:
                        self.logger.warning('httpx.RemoteProtocolError: the server has disconnected, retrying')
                    continue
                raise e
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                if response:
                    response.close()
                raise e
        return response  # type: ignore

    def close(self):
        self.client.close()

    @property
    def is_closed(self) -> bool:
        return self.client.is_closed

    def _new_client(self):
        limit = httpx.Limits(
            max_connections=self.max_connections,
            max_keepalive_connections=self.max_keepalive_connections,
            keepalive_expiry=self.keepalive_expiry,
        )
        # See https://www.python-httpx.org/advanced/#routing
        mounts = {}
        for pattern, proxy_url in self.proxies.items():
            if not self.enable_http and pattern.startswith('http://'):
                continue
            if (
                proxy_url.startswith('socks4://')
                or proxy_url.startswith('socks5://')
                or proxy_url.startswith('socks5h://')
            ):
                mounts[pattern] = _get_transport_for_socks_proxy(
                    self.verify, self.enable_http2, self.local_address, proxy_url, limit, 0
                )
            else:
                mounts[pattern] = _get_transport(
                    self.verify, self.enable_http2, self.local_address, proxy_url, limit, 0
                )

        if not self.enable_http:
            mounts['http://'] = _HTTPTransportNoHttp()

        transport = _get_transport(self.verify, self.enable_http2, self.local_address, None, limit, 0)

        event_hooks = None
        if self.hook_log_response:
            event_hooks = {'response': [self.hook_log_response]}
        self.client = httpx.Client(
            transport=transport,
            mounts=mounts,
            max_redirects=self.max_redirects,
            event_hooks=event_hooks,
        )

    def _reconnect_client(self):
        self.client.close()
        self._new_client()

    def _patch_request(self, kwargs):
        # see https://www.python-httpx.org/compatibility/#redirects
        follow_redirects = self.allow_redirects
        if 'allow_redirects' in kwargs:
            # see https://github.com/encode/httpx/pull/1808
            follow_redirects = kwargs.pop('allow_redirects')
        kwargs['follow_redirects'] = follow_redirects

    def _patch_response(self, response):
        if isinstance(response, httpx.Response):
            # requests compatibility (response is not streamed)
            # see also https://www.python-httpx.org/compatibility/#checking-for-4xx5xx-responses
            response.ok = not response.is_error  # type: ignore

        return response


_HTTPMultiClientConf = namedtuple('HTTPMultiClientConf', ['verify', 'max_redirects'])


class BaseHTTPClient(ABCHTTPClient):
    """Some parameter like verify, max_redirects are defined at the client level,
    not at the request level.

    This class allow to specify these parameters at the request level.
    The implementation uses multiple instances of OneHTTPClient

    This class does not deal with the retry_on_http_error parameter
    """

    def __init__(
        self,
        **default_kwargs,
    ):
        # set the default values
        self.default = _HTTPMultiClientConf(True, 30)
        # extract the values from the HTTPCient constructor
        # the line before is mandatory to be able to self._extract_kwargs_clients
        # and keep the other arguments
        self.default, self.default_kwargs = self._extract_kwargs_clients(default_kwargs)
        self.clients: Dict[Tuple, OneHTTPClient] = {}

    def close(self):
        for client in self.clients.values():
            client.close()

    @property
    def is_closed(self) -> bool:
        return all(client.is_closed for client in self.clients.values())

    # send(... ,foo=1, bar=2)
    def send(self, stream, method, url, timeout=None, **kwargs):
        client = self._get_client_and_update_kwargs(kwargs)
        return client.send(stream, method, url, timeout, **kwargs)

    def _get_client_and_update_kwargs(self, kwargs) -> OneHTTPClient:
        # extract HTTPMultiClientConf using the parameter in the request
        # and fallback to the parameters defined in the constructor
        # = the parameters set in the network settings
        http_multi_client_conf, kwargs = self._extract_kwargs_clients(kwargs)
        if http_multi_client_conf not in self.clients:
            self.clients[http_multi_client_conf] = OneHTTPClient(
                verify=http_multi_client_conf.verify,
                max_redirects=http_multi_client_conf.max_redirects,
                **self.default_kwargs,
            )
        return self.clients[http_multi_client_conf]

    def _extract_kwargs_clients(self, kwargs) -> Tuple[_HTTPMultiClientConf, Dict]:
        # default values
        # see https://www.python-httpx.org/compatibility/#ssl-configuration
        verify = kwargs.pop('verify', NOTSET)
        max_redirects = kwargs.pop('max_redirects', NOTSET)
        if verify == NOTSET:
            verify = self.default.verify
        if max_redirects == NOTSET:
            max_redirects = self.default.max_redirects
        return _HTTPMultiClientConf(verify, max_redirects), kwargs


class HTTPClient(BaseHTTPClient):
    """Inherit from BaseHTTPClient, raise an exception according to the retry_on_http_error parameter"""

    def __init__(self, retry_on_http_error=None, **kwargs):
        super().__init__(**kwargs)
        self.retry_on_http_error = retry_on_http_error
        self._check_configuration()

    def _check_configuration(self):
        # make sure we can create at least an OneHTTPClient without exception
        self._get_client_and_update_kwargs({})

    def send(self, stream, method, url, timeout=None, **kwargs):
        try:
            do_raise_for_httperror = self._extract_do_raise_for_httperror(kwargs)
            response = super().send(stream, method, url, timeout=timeout, **kwargs)
            if do_raise_for_httperror:
                raise_for_httperror(response)
            if self._is_error_but_retry(response):
                raise SoftRetryHTTPException(response)
            return response
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            raise e

    def _is_error_but_retry(self, response):
        # pylint: disable=too-many-boolean-expressions
        return (
            (self.retry_on_http_error is True and 400 <= response.status_code <= 599)
            or (isinstance(self.retry_on_http_error, list) and response.status_code in self.retry_on_http_error)
            or (isinstance(self.retry_on_http_error, int) and response.status_code == self.retry_on_http_error)
        )

    @staticmethod
    def _extract_do_raise_for_httperror(kwargs):
        do_raise_for_httperror = True
        if 'raise_for_httperror' in kwargs:
            do_raise_for_httperror = kwargs['raise_for_httperror']
            del kwargs['raise_for_httperror']
        return do_raise_for_httperror

    def __repr__(self):
        keys_values = " ".join([f"{k}={v!r}" for k, v in self.default_kwargs.items()])
        return f"<{self.__class__.__name__} retry_on_http_error={self.retry_on_http_error!r} {keys_values}>"


class TorHTTPClient(HTTPClient):
    """Extend HTTPClientSoftError client. To use with Tor configuration.

    The class checks if the client is really connected through Tor.
    """

    _TOR_CHECK_RESULT = {}

    def __init__(self, proxies=None, local_addresses=None, **kwargs):
        self.proxies = proxies
        self.local_addresses = local_addresses
        super().__init__(proxies=proxies, local_addresses=local_addresses, **kwargs)

    def _check_configuration(self):
        if not self._is_connected_through_tor(self.proxies, self.local_addresses):
            self.close()
            raise httpx.HTTPError('Network configuration problem: not using Tor')

    def _is_connected_through_tor(self, proxies, local_addresses) -> bool:
        """TODO : rewrite to check the proxies variable instead of checking the HTTPTransport ?"""
        if proxies is None:
            return False

        cache_key = (local_addresses, tuple(proxies.items()))
        if cache_key in TorHTTPClient._TOR_CHECK_RESULT:
            return TorHTTPClient._TOR_CHECK_RESULT[cache_key]

        # False is the client use the DNS from the proxy
        use_local_dns = False

        # get one httpx client through get_client_and_update_kwargs
        one_http_client = self._get_client_and_update_kwargs({"verify": True})
        httpx_client = one_http_client.client
        # ignore client._transport because it is not used with all://
        for transport in httpx_client._mounts.values():  # pylint: disable=protected-access
            if isinstance(transport, _HTTPTransportNoHttp):
                # ignore the NO HTTP transport
                continue
            if isinstance(transport, _CustomSyncProxyTransport) and not getattr(
                transport._pool, "_rdns", False  # pylint: disable=protected-access # type: ignore
            ):
                # socks5:// with local DNS
                # expect socks5h:// with remote DNS to resolve .onion domain.
                use_local_dns = True
                break

        #
        if use_local_dns:
            # no test
            result = False
        else:
            # actual check
            response = one_http_client.request("GET", "https://check.torproject.org/api/ip", timeout=60)
            if response.status_code != 200:
                result = False
            else:
                result = bool(response.json().get("IsTor", False))
        TorHTTPClient._TOR_CHECK_RESULT[cache_key] = result
        return result

    @staticmethod
    def _clear_cache():
        """Only for the tests"""
        TorHTTPClient._TOR_CHECK_RESULT = {}
