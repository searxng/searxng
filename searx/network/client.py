# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring, global-statement

import typing as t

import asyncio
import logging
import random
from ssl import SSLContext
import threading

import httpx2

CertTypes = str | tuple[str, str] | tuple[str, str, str]
SslContextKeyType = tuple[str | None, CertTypes | None, bool, bool]

LOOP: asyncio.AbstractEventLoop = None  # pyright: ignore[reportAssignmentType]

SSLCONTEXTS: dict[SslContextKeyType, SSLContext] = {}


def shuffle_ciphers(ssl_context: SSLContext):
    """Shuffle httpx2's default ciphers of a SSL context randomly.

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
    c_list = [cipher["name"] for cipher in ssl_context.get_ciphers()]
    sc_list, c_list = c_list[:3], c_list[3:]
    random.shuffle(c_list)
    ssl_context.set_ciphers(":".join(sc_list + c_list))


def get_sslcontexts(
    proxy_url: str | None = None, cert: CertTypes | None = None, verify: bool = True, trust_env: bool = True
) -> SSLContext:
    key: SslContextKeyType = (proxy_url, cert, verify, trust_env)
    if key not in SSLCONTEXTS:
        SSLCONTEXTS[key] = httpx2.create_ssl_context(verify, cert, trust_env)
    shuffle_ciphers(SSLCONTEXTS[key])
    return SSLCONTEXTS[key]


class AsyncHTTPTransportNoHttp(httpx2.AsyncBaseTransport):
    """Reject ``http://`` requests (used when ``enable_http`` is false)."""

    async def handle_async_request(self, request: httpx2.Request):
        raise httpx2.UnsupportedProtocol('HTTP protocol is disabled')


def get_transport(
    verify: bool, http2: bool, local_address: str, proxy_url: str | None, limit: httpx2.Limits, retries: int
):
    _verify = get_sslcontexts(proxy_url, None, verify, True) if verify is True else verify
    return httpx2.AsyncHTTPTransport(
        verify=_verify,
        http2=http2,
        limits=limit,
        proxy=proxy_url,
        local_address=local_address,
        retries=retries,
    )


def new_client(
    # pylint: disable=too-many-arguments
    enable_http: bool,
    verify: bool,
    enable_http2: bool,
    max_connections: int,
    max_keepalive_connections: int,
    keepalive_expiry: float,
    proxies: dict[str, str],
    local_address: str,
    retries: int,
    max_redirects: int,
    hook_log_response: t.Callable[..., t.Any] | None,
) -> httpx2.AsyncClient:
    limit = httpx2.Limits(
        max_connections=max_connections,
        max_keepalive_connections=max_keepalive_connections,
        keepalive_expiry=keepalive_expiry,
    )
    # See https://httpx2.pydantic.dev/advanced/transports/#routing
    mounts: dict[str, httpx2.AsyncBaseTransport] = {}
    for pattern, proxy_url in proxies.items():
        if not enable_http and pattern.startswith('http://'):
            continue
        mounts[pattern] = get_transport(verify, enable_http2, local_address, proxy_url, limit, retries)

    if not enable_http:
        mounts['http://'] = AsyncHTTPTransportNoHttp()

    transport = get_transport(verify, enable_http2, local_address, None, limit, retries)

    event_hooks = None
    if hook_log_response:
        event_hooks = {'response': [hook_log_response]}

    return httpx2.AsyncClient(
        transport=transport,
        mounts=mounts,
        max_redirects=max_redirects,
        event_hooks=event_hooks,
    )


def get_loop() -> asyncio.AbstractEventLoop:
    return LOOP


def init():
    # log
    for logger_name in (
        'httpx2',
        'httpcore2.proxy',
        'httpcore2.connection',
        'httpcore2.http11',
        'httpcore2.http2',
        'httpcore2.socks',
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
