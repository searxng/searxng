# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=missing-module-docstring, global-statement

import asyncio
import logging
from ssl import SSLContext
import threading
from typing import Any, Dict

import httpx
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
TRANSPORT_KWARGS = {
    'trust_env': False,
}


def get_sslcontexts(proxy_url=None, cert=None, verify=True, trust_env=True, http2=False):
    key = (proxy_url, cert, verify, trust_env, http2)
    if key not in SSLCONTEXTS:
        SSLCONTEXTS[key] = httpx.create_ssl_context(cert, verify, trust_env, http2)
    return SSLCONTEXTS[key]


class AsyncHTTPTransportNoHttp(httpx.AsyncHTTPTransport):
    """Block HTTP request"""

    async def handle_async_request(self, request):
        raise httpx.UnsupportedProtocol('HTTP protocol is disabled')


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


def get_transport_for_socks_proxy(verify, http2, local_address, proxy_url, limit, retries):
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
    verify = get_sslcontexts(proxy_url, None, True, False, http2) if verify is True else verify
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
        **TRANSPORT_KWARGS,
    )


def get_transport(verify, http2, local_address, proxy_url, limit, retries):
    verify = get_sslcontexts(None, None, True, False, http2) if verify is True else verify
    return httpx.AsyncHTTPTransport(
        # pylint: disable=protected-access
        verify=verify,
        http2=http2,
        limits=limit,
        proxy=httpx._config.Proxy(proxy_url) if proxy_url else None,
        local_address=local_address,
        retries=retries,
        **TRANSPORT_KWARGS,
    )


def new_client(
    # pylint: disable=too-many-arguments
    enable_http,
    verify,
    enable_http2,
    max_connections,
    max_keepalive_connections,
    keepalive_expiry,
    proxies,
    local_address,
    retries,
    max_redirects,
    hook_log_response,
):
    limit = httpx.Limits(
        max_connections=max_connections,
        max_keepalive_connections=max_keepalive_connections,
        keepalive_expiry=keepalive_expiry,
    )
    # See https://www.python-httpx.org/advanced/#routing
    mounts = {}
    for pattern, proxy_url in proxies.items():
        if not enable_http and pattern.startswith('http://'):
            continue
        if proxy_url.startswith('socks4://') or proxy_url.startswith('socks5://') or proxy_url.startswith('socks5h://'):
            mounts[pattern] = get_transport_for_socks_proxy(
                verify, enable_http2, local_address, proxy_url, limit, retries
            )
        else:
            mounts[pattern] = get_transport(verify, enable_http2, local_address, proxy_url, limit, retries)

    if not enable_http:
        mounts['http://'] = AsyncHTTPTransportNoHttp()

    transport = get_transport(verify, enable_http2, local_address, None, limit, retries)

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
