# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=missing-module-docstring, global-statement

import asyncio
import logging
import threading
import httpcore
import httpx
from httpx_socks import AsyncProxyTransport
from python_socks import (
    parse_proxy_url,
    ProxyConnectionError,
    ProxyTimeoutError,
    ProxyError
)

from searx import logger

# Optional uvloop (support Python 3.6)
try:
    import uvloop
except ImportError:
    pass
else:
    uvloop.install()


logger = logger.getChild('searx.http.client')
LOOP = None
SSLCONTEXTS = {}
TRANSPORT_KWARGS = {
    'backend': 'asyncio',
    'trust_env': False,
}


# pylint: disable=protected-access
async def close_connections_for_url(
        connection_pool: httpcore.AsyncConnectionPool,
        url: httpcore._utils.URL ):

    origin = httpcore._utils.url_to_origin(url)
    logger.debug('Drop connections for %r', origin)
    connections_to_close = connection_pool._connections_for_origin(origin)
    for connection in connections_to_close:
        await connection_pool._remove_from_pool(connection)
        try:
            await connection.aclose()
        except httpcore.NetworkError as e:
            logger.warning('Error closing an existing connection', exc_info=e)
# pylint: enable=protected-access


def get_sslcontexts(proxy_url=None, cert=None, verify=True, trust_env=True, http2=False):
    global SSLCONTEXTS
    key = (proxy_url, cert, verify, trust_env, http2)
    if key not in SSLCONTEXTS:
        SSLCONTEXTS[key] = httpx.create_ssl_context(cert, verify, trust_env, http2)
    return SSLCONTEXTS[key]


class AsyncHTTPTransportNoHttp(httpcore.AsyncHTTPTransport):
    """Block HTTP request"""

    async def arequest(self, method, url, headers=None, stream=None, ext=None):
        raise httpcore.UnsupportedProtocol("HTTP protocol is disabled")


class AsyncProxyTransportFixed(AsyncProxyTransport):
    """Fix httpx_socks.AsyncProxyTransport

    Map python_socks exceptions to httpcore.ProxyError

    Map socket.gaierror to httpcore.ConnectError

    Note: keepalive_expiry is ignored, AsyncProxyTransport should call:
    * self._keepalive_sweep()
    * self._response_closed(self, connection)

    Note: AsyncProxyTransport inherit from AsyncConnectionPool

    Note: the API is going to change on httpx 0.18.0
    see https://github.com/encode/httpx/pull/1522
    """

    async def arequest(self, method, url, headers=None, stream=None, ext=None):
        retry = 2
        while retry > 0:
            retry -= 1
            try:
                return await super().arequest(method, url, headers, stream, ext)
            except (ProxyConnectionError, ProxyTimeoutError, ProxyError) as e:
                raise httpcore.ProxyError(e)
            except OSError as e:
                # socket.gaierror when DNS resolution fails
                raise httpcore.NetworkError(e)
            except httpcore.RemoteProtocolError as e:
                # in case of httpcore.RemoteProtocolError: Server disconnected
                await close_connections_for_url(self, url)
                logger.warning('httpcore.RemoteProtocolError: retry', exc_info=e)
                # retry
            except (httpcore.NetworkError, httpcore.ProtocolError) as e:
                # httpcore.WriteError on HTTP/2 connection leaves a new opened stream
                # then each new request creates a new stream and raise the same WriteError
                await close_connections_for_url(self, url)
                raise e


class AsyncHTTPTransportFixed(httpx.AsyncHTTPTransport):
    """Fix httpx.AsyncHTTPTransport"""

    async def arequest(self, method, url, headers=None, stream=None, ext=None):
        retry = 2
        while retry > 0:
            retry -= 1
            try:
                return await super().arequest(method, url, headers, stream, ext)
            except OSError as e:
                # socket.gaierror when DNS resolution fails
                raise httpcore.ConnectError(e)
            except httpcore.CloseError as e:
                # httpcore.CloseError: [Errno 104] Connection reset by peer
                # raised by _keepalive_sweep()
                #   from https://github.com/encode/httpcore/blob/4b662b5c42378a61e54d673b4c949420102379f5/httpcore/_backends/asyncio.py#L198  # pylint: disable=line-too-long
                await close_connections_for_url(self._pool, url)
                logger.warning('httpcore.CloseError: retry', exc_info=e)
                # retry
            except httpcore.RemoteProtocolError as e:
                # in case of httpcore.RemoteProtocolError: Server disconnected
                await close_connections_for_url(self._pool, url)
                logger.warning('httpcore.RemoteProtocolError: retry', exc_info=e)
                # retry
            except (httpcore.ProtocolError, httpcore.NetworkError) as e:
                await close_connections_for_url(self._pool, url)
                raise e


def get_transport_for_socks_proxy(verify, http2, local_address, proxy_url, limit, retries):
    global TRANSPORT_KWARGS
    # support socks5h (requests compatibility):
    # https://requests.readthedocs.io/en/master/user/advanced/#socks
    # socks5://   hostname is resolved on client side
    # socks5h://  hostname is resolved on proxy side
    rdns = False
    socks5h = 'socks5h://'
    if proxy_url.startswith(socks5h):
        proxy_url = 'socks5://' + proxy_url[len(socks5h):]
        rdns = True

    proxy_type, proxy_host, proxy_port, proxy_username, proxy_password = parse_proxy_url(proxy_url)
    verify = get_sslcontexts(proxy_url, None, True, False, http2) if verify is True else verify
    return AsyncProxyTransportFixed(
        proxy_type=proxy_type, proxy_host=proxy_host, proxy_port=proxy_port,
        username=proxy_username, password=proxy_password,
        rdns=rdns,
        loop=get_loop(),
        verify=verify,
        http2=http2,
        local_address=local_address,
        max_connections=limit.max_connections,
        max_keepalive_connections=limit.max_keepalive_connections,
        keepalive_expiry=limit.keepalive_expiry,
        retries=retries,
        **TRANSPORT_KWARGS
    )


def get_transport(verify, http2, local_address, proxy_url, limit, retries):
    global TRANSPORT_KWARGS
    verify = get_sslcontexts(None, None, True, False, http2) if verify is True else verify
    return AsyncHTTPTransportFixed(
        # pylint: disable=protected-access
        verify=verify,
        http2=http2,
        local_address=local_address,
        proxy=httpx._config.Proxy(proxy_url) if proxy_url else None,
        limits=limit,
        retries=retries,
        **TRANSPORT_KWARGS
    )


def iter_proxies(proxies):
    # https://www.python-httpx.org/compatibility/#proxy-keys
    if isinstance(proxies, str):
        yield 'all://', proxies
    elif isinstance(proxies, dict):
        for pattern, proxy_url in proxies.items():
            yield pattern, proxy_url


def new_client(
        # pylint: disable=too-many-arguments
        enable_http, verify, enable_http2,
        max_connections, max_keepalive_connections, keepalive_expiry,
        proxies, local_address, retries, max_redirects, hook_log_response  ):
    limit = httpx.Limits(
        max_connections=max_connections,
        max_keepalive_connections=max_keepalive_connections,
        keepalive_expiry=keepalive_expiry
    )
    # See https://www.python-httpx.org/advanced/#routing
    mounts = {}
    for pattern, proxy_url in iter_proxies(proxies):
        if not enable_http and (pattern == 'http' or pattern.startswith('http://')):
            continue
        if (proxy_url.startswith('socks4://')
           or proxy_url.startswith('socks5://')
            or proxy_url.startswith('socks5h://')
        ):
            mounts[pattern] = get_transport_for_socks_proxy(
                verify, enable_http2, local_address, proxy_url, limit, retries
            )
        else:
            mounts[pattern] = get_transport(
                verify, enable_http2, local_address, proxy_url, limit, retries
            )

    if not enable_http:
        mounts['http://'] = AsyncHTTPTransportNoHttp()

    transport = get_transport(verify, enable_http2, local_address, None, limit, retries)

    event_hooks = None
    if hook_log_response:
        event_hooks = {'response': [ hook_log_response ]}

    return httpx.AsyncClient(
        transport=transport,
        mounts=mounts,
        max_redirects=max_redirects,
        event_hooks=event_hooks,
    )


def get_loop():
    global LOOP
    return LOOP


def init():
    # log
    for logger_name in ('hpack.hpack', 'hpack.table', 'httpx._client'):
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
