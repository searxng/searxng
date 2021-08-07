# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring, missing-function-docstring, global-statement

import asyncio
import threading
import logging
from typing import Optional

import aiohttp
from aiohttp.client_reqrep import ClientRequest
from aiohttp_socks import ProxyConnector
from requests.models import InvalidURL

from yarl import URL

# Optional uvloop (support Python 3.6)
try:
    import uvloop
except ImportError:
    pass
else:
    uvloop.install()


logger = logging.getLogger('searx.http.client')
LOOP: Optional[asyncio.AbstractEventLoop] = None
RESOLVER: Optional[aiohttp.ThreadedResolver] = None


class ClientRequestNoHttp(ClientRequest):

    def __init__(self, method: str, url: URL, *args, **kwargs):
        if url.scheme == 'http':
            raise InvalidURL(url)
        super().__init__(method, url, *args, **kwargs)


def new_client(
        # pylint: disable=too-many-arguments
        enable_http, verify, max_connections, max_keepalive_connections, keepalive_expiry,
        proxy_url, local_address):
    # connector
    conn_kwargs = {
        'ssl': verify,
        'keepalive_timeout': keepalive_expiry or 15,
        'limit': max_connections,
        'limit_per_host': max_keepalive_connections,
        'loop': LOOP,
    }
    if local_address:
        conn_kwargs['local_addr'] = (local_address, 0)

    if not proxy_url:
        conn_kwargs['resolver'] = RESOLVER
        connector = aiohttp.TCPConnector(**conn_kwargs)
    else:
        # support socks5h (requests compatibility):
        # https://requests.readthedocs.io/en/master/user/advanced/#socks
        # socks5://   hostname is resolved on client side
        # socks5h://  hostname is resolved on proxy side
        rdns = False
        socks5h = 'socks5h://'
        if proxy_url.startswith(socks5h):
            proxy_url = 'socks5://' + proxy_url[len(socks5h):]
            rdns = True
        else:
            conn_kwargs['resolver'] = RESOLVER
        connector = ProxyConnector.from_url(proxy_url, rdns=rdns, **conn_kwargs)
    # client
    session_kwargs = {}
    if enable_http:
        session_kwargs['request_class'] = ClientRequestNoHttp
    return aiohttp.ClientSession(connector=connector, **session_kwargs)


def get_loop():
    global LOOP
    return LOOP


def init():
    # loop
    def loop_thread():
        global LOOP, RESOLVER
        LOOP = asyncio.new_event_loop()
        RESOLVER = aiohttp.resolver.DefaultResolver(LOOP)
        LOOP.run_forever()

    thread = threading.Thread(
        target=loop_thread,
        name='asyncio_loop',
        daemon=True,
    )
    thread.start()


init()
