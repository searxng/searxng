# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring, global-statement

from __future__ import annotations

import asyncio
import contextlib
import logging
import random
from ssl import SSLContext
import threading
from typing import Any, Dict, Iterable

import httpx
import httpcore
from httpx_socks import AsyncProxyTransport
from python_socks import parse_proxy_url, ProxyConnectionError, ProxyTimeoutError, ProxyError

from searx import logger

# Optional uvloop (support Python 3.6)
try:
    import uvloop
except ImportError:
    pass
else:
    uvloop.install()


logger = logger.getChild('searx.network.client')
LOOP = None
SSLCONTEXTS: Dict[Any, SSLContext] = {}


def shuffle_ciphers(ssl_context):
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


def get_sslcontexts(proxy_url=None, cert=None, verify=True, trust_env=True, http2=False):
    key = (proxy_url, cert, verify, trust_env, http2)
    if key not in SSLCONTEXTS:
        SSLCONTEXTS[key] = httpx.create_ssl_context(cert, verify, trust_env, http2)
    shuffle_ciphers(SSLCONTEXTS[key])
    return SSLCONTEXTS[key]


class AsyncHTTPTransportNoHttp(httpx.AsyncHTTPTransport):
    """Block HTTP request

    The constructor is blank because httpx.AsyncHTTPTransport.__init__ creates an SSLContext unconditionally:
    https://github.com/encode/httpx/blob/0f61aa58d66680c239ce43c8cdd453e7dc532bfc/httpx/_transports/default.py#L271

    Each SSLContext consumes more than 500kb of memory, since there is about one network per engine.

    In consequence, this class overrides all public methods

    For reference: https://github.com/encode/httpx/issues/2298
    """

    def __init__(self, *args, **kwargs):
        # pylint: disable=super-init-not-called
        # this on purpose if the base class is not called
        pass

    async def handle_async_request(self, request):
        raise httpx.UnsupportedProtocol('HTTP protocol is disabled')

    async def aclose(self) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(
        self,
        exc_type=None,
        exc_value=None,
        traceback=None,
    ) -> None:
        pass


class AsyncProxyTransportFixed(AsyncProxyTransport):
    """Fix httpx_socks.AsyncProxyTransport

    Map python_socks exceptions to httpx.ProxyError exceptions
    """

    async def handle_async_request(self, request):
        try:
            return await super().handle_async_request(request)
        except ProxyConnectionError as e:
            raise httpx.ProxyError("ProxyConnectionError: " + e.strerror, request=request) from e
        except ProxyTimeoutError as e:
            raise httpx.ProxyError("ProxyTimeoutError: " + e.args[0], request=request) from e
        except ProxyError as e:
            raise httpx.ProxyError("ProxyError: " + e.args[0], request=request) from e


def get_socks_transport(verify, http2, local_address, proxy_url, limit, retries):
    """Return an AsyncProxyTransport."""
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
    verify = get_sslcontexts(proxy_url, None, verify, True, http2) if verify is True else verify
    return AsyncProxyTransportFixed(
        proxy_type=proxy_type,
        proxy_host=proxy_host,
        proxy_port=proxy_port,
        username=proxy_username,
        password=proxy_password,
        rdns=rdns,
        loop=get_loop(),
        verify=verify,
        http2=http2,
        local_address=local_address,
        limits=limit,
        retries=retries,
    )


def get_http_transport(verify, http2, local_address, proxy_url, limit, retries):
    """Return an AsyncHTTPTransport."""
    verify = get_sslcontexts(None, None, verify, True, http2) if verify is True else verify
    return httpx.AsyncHTTPTransport(
        # pylint: disable=protected-access
        verify=verify,
        http2=http2,
        limits=limit,
        proxy=httpx._config.Proxy(proxy_url) if proxy_url else None,
        local_address=local_address,
        retries=retries,
    )


def get_single_transport(
    limit: httpx.Limits | None = None,
    proxy_url: str | None = None,
    local_address: str | None = None,
    retries: int = 0,
    *,
    verify: bool = True,
    http2: bool = True,
) -> httpx.AsyncBaseTransport:
    """Generate a single, non-parallel transport.

    Parameters
    ----------
    limit : httpx.Limits
        Limits applied to the to the transport.
    proxy_url : str | None, optional
        Proxy to use for the transport.
    local_address : str | None, optional
        local address to specify in the connection.
    retries : int, optional
        how many times to retry the request, by default 0
    verify : bool, optional
        Verify the certificates, by default True
    http2 : bool, optional
        Enable HTTP2 protocol, by default True

    Returns
    -------
    httpx.AsyncBaseTransport
        An async transport object.
    """
    limit = limit or httpx.Limits()
    if proxy_url and proxy_url.startswith(('socks4://', 'socks5://', 'socks5h://')):
        return get_socks_transport(verify, http2, local_address, proxy_url, limit, retries)
    return get_http_transport(verify, http2, local_address, proxy_url, limit, retries)


class AsyncParallelTransport(httpx.AsyncBaseTransport):
    """Fan out request to multiple base transports."""

    def __init__(
        self,
        transports: Iterable[httpx.AsyncBaseTransport],
        proxy_request_redundancy: int,
        network_logger: logging.Logger,
    ) -> None:
        """Init the parallel transport using a list of base `transports`."""
        self._transports = list(transports)
        if len(self._transports) == 0:
            msg = "Got an empty list of (proxy) transports."
            raise ValueError(msg)
        if proxy_request_redundancy < 1:
            logger.warning("Invalid proxy_request_redundancy specified: %d", proxy_request_redundancy)
            proxy_request_redundancy = 1
        self._proxy_request_redundancy = proxy_request_redundancy
        self._index = random.randrange(len(self._transports))  # noqa: S311
        self._logger = network_logger or logger

    async def handle_async_request(
        self,
        request: httpx.Request,
    ) -> httpx.Response:
        # pylint: disable=too-many-branches
        """Issue parallel requests to all sub-transports.

        Return the response of the first completed.

        Parameters
        ----------
        request : httpx.Request
            Request to pass to the transports.

        Returns
        -------
        httpx.Response
            Response from the first completed request.

        """
        response = None  # non-error response, taking precedence
        error_response = None  # any error response
        request_error = None  # any request related exception
        tcount = len(self._transports)
        redundancy = self._proxy_request_redundancy
        pending = [
            asyncio.create_task(self._transports[i % tcount].handle_async_request(request))
            for i in range(self._index, self._index + redundancy)
        ]
        self._index = (self._index + redundancy) % tcount
        while pending:
            if len(pending) == 1:
                return await pending.pop()
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                try:
                    result = task.result()
                    if not result.is_error:
                        response = result
                    elif result.status_code == 404 and response is None:
                        response = result
                    elif not error_response:
                        self._logger.warning("Error response: %s for %s", result.status_code, request.url)
                        error_response = result
                except (
                    httpx.HTTPError,
                    httpcore.ProtocolError,
                    httpcore.NetworkError,
                    httpcore.TimeoutException,
                    # Low level semaphore errors.
                    ValueError,
                ) as e:
                    if not request_error:
                        self._logger.warning("Request error: %s for %s", e, request.url)
                        request_error = e
            if response:
                break
        if pending:
            with contextlib.suppress(asyncio.exceptions.CancelledError):
                gather = asyncio.gather(*pending)
                gather.cancel()
                self._logger.debug("Cancelling %d/%d redundant proxy requests.", len(pending), redundancy)
                await gather
        if response:
            return response
        if error_response:
            return error_response
        msg = "No valid response."
        if request_error:
            raise httpx.RequestError(msg) from request_error
        raise httpx.RequestError(msg)

    async def aclose(self) -> None:
        """Close all the transports."""
        for transport in self._transports:
            await transport.aclose()


def get_transport(
    proxy_urls: list,
    limit: httpx.Limits | None = None,
    local_address: str | None = None,
    proxy_request_redundancy: int = 1,
    retries: int = 0,
    network_logger: logging.Logger = logger,
    *,
    verify: bool = True,
    http2: bool = True,
) -> httpx.AsyncBaseTransport:
    """Return a single http/proxy transport or the parallel version of those."""
    limit = limit or httpx.Limits()
    # pylint: disable=unnecessary-lambda-assignment
    transport = lambda proxy_url: get_single_transport(
        verify=verify,
        http2=http2,
        local_address=local_address,
        proxy_url=proxy_url,
        limit=limit,
        retries=retries,
    )
    if len(proxy_urls or []) <= 1:
        return transport(proxy_urls[0] if proxy_urls else None)
    return AsyncParallelTransport(map(transport, proxy_urls), proxy_request_redundancy, network_logger)


def new_client(
    # pylint: disable=too-many-arguments
    enable_http,
    verify,
    enable_http2,
    max_connections,
    max_keepalive_connections,
    keepalive_expiry,
    proxies,
    proxy_request_redundancy,
    local_address,
    retries,
    max_redirects,
    hook_log_response,
    network_logger,
):
    limit = httpx.Limits(
        max_connections=max_connections,
        max_keepalive_connections=max_keepalive_connections,
        keepalive_expiry=keepalive_expiry,
    )
    # See https://www.python-httpx.org/advanced/#routing
    mounts = {}
    for pattern, proxy_urls in proxies.items():
        if not enable_http and pattern.startswith('http://'):
            continue
        mounts[pattern] = get_transport(
            verify=verify,
            http2=enable_http2,
            local_address=local_address,
            proxy_urls=proxy_urls,
            proxy_request_redundancy=proxy_request_redundancy,
            limit=limit,
            retries=retries,
            network_logger=network_logger,
        )

    if not enable_http:
        mounts['http://'] = AsyncHTTPTransportNoHttp()

    transport = get_http_transport(verify, enable_http2, local_address, None, limit, retries)

    event_hooks = None
    if hook_log_response:
        event_hooks = {'response': [hook_log_response]}

    return httpx.AsyncClient(
        transport=transport,
        mounts=mounts,
        max_redirects=max_redirects,
        event_hooks=event_hooks,
    )


def get_loop():
    return LOOP


def init():
    # log
    for logger_name in (
        'httpx',
        'httpcore.proxy',
        'httpcore.connection',
        'httpcore.http11',
        'httpcore.http2',
        'hpack.hpack',
        'hpack.table',
    ):
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    # loop
    def loop_thread():
        global LOOP
        LOOP = asyncio.new_event_loop()
        LOOP.run_forever()

    thread = threading.Thread(
        target=loop_thread,
        name='asyncio_loop',
        daemon=True,
    )
    thread.start()


init()
