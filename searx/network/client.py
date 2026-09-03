# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring, global-statement

import typing as t

import asyncio
import logging
import os
import threading

from curl_cffi import AsyncSession, CurlHttpVersion, CurlOpt
from curl_cffi.requests.exceptions import InvalidSchema, RequestException

from searx.extended_types import SXNG_Response

LOOP: asyncio.AbstractEventLoop = None  # pyright: ignore[reportAssignmentType]

# chrome is used by default
DEFAULT_IMPERSONATE = "chrome"
NO_IMPERSONATE = "none"


class AsyncClient(AsyncSession):
    """:class:`curl_cffi.AsyncSession` with ``aclose`` / ``is_closed``."""

    def __init__(self, enable_http: bool, **kwargs: t.Any):
        self.enable_http = enable_http
        self._closed = False
        super().__init__(**kwargs)

    @property
    def is_closed(self) -> bool:
        return self._closed

    def check_url(self, url: str) -> None:
        if not self.enable_http and str(url).startswith("http://"):
            raise InvalidSchema("HTTP protocol is disabled")

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            await self.close()
        except RequestException:
            pass


def _proxy_kwargs(proxies: dict[str, str], enable_http: bool) -> dict[str, t.Any]:
    """Map settings.yml proxy keys (``all://``, ``https://``) to curl_cffi."""
    mapped: dict[str, str] = {}
    all_proxy: str | None = None
    for pattern, proxy_url in proxies.items():
        if not enable_http and pattern.startswith("http://"):
            continue
        if pattern.startswith("https"):
            mapped["https"] = proxy_url
        elif pattern.startswith("http"):
            mapped["http"] = proxy_url
        else:
            all_proxy = proxy_url
    if all_proxy:
        return {"proxy": all_proxy}
    if mapped:
        return {"proxies": mapped}
    return {}


def new_client(
    # pylint: disable=too-many-arguments
    enable_http: bool,
    verify: bool | str,
    enable_http2: bool,
    enable_http3: bool,
    max_connections: int,
    proxies: dict[str, str],
    local_address: str | None,
    max_redirects: int,
    impersonate: str = DEFAULT_IMPERSONATE,
    curl_options: dict[int, t.Any] | None = None,
) -> AsyncClient:
    extra_curl = dict(curl_options or {})
    cert_file = os.environ.get("SSL_CERT_FILE")
    if cert_file:
        extra_curl.setdefault(CurlOpt.CAINFO, cert_file)
    cert_dir = os.environ.get("SSL_CERT_DIR")
    if cert_dir:
        extra_curl.setdefault(CurlOpt.CAPATH, cert_dir)
    use_impersonate = impersonate not in ("", NO_IMPERSONATE)
    kwargs: dict[str, t.Any] = {
        "enable_http": enable_http,
        "verify": verify,
        "max_redirects": max_redirects,
        "max_clients": max_connections or 10,
        "response_class": SXNG_Response,
        "discard_cookies": True,
        **_proxy_kwargs(proxies, enable_http),
    }
    if use_impersonate:
        kwargs["impersonate"] = impersonate
        kwargs["default_headers"] = True
    if local_address:
        kwargs["interface"] = local_address
    if not enable_http2:
        kwargs["http_version"] = CurlHttpVersion.V1_1
    elif enable_http3 and not proxies:
        kwargs["http_version"] = CurlHttpVersion.V3
    else:
        kwargs["http_version"] = CurlHttpVersion.V2_0
    if extra_curl:
        kwargs["curl_options"] = extra_curl
    return AsyncClient(**kwargs)


def get_loop() -> asyncio.AbstractEventLoop:
    return LOOP


def init():
    logging.getLogger("curl_cffi").setLevel(logging.WARNING)

    ready = threading.Event()

    def loop_thread():
        global LOOP
        LOOP = asyncio.new_event_loop()
        ready.set()
        LOOP.run_forever()

    threading.Thread(target=loop_thread, name="asyncio_loop", daemon=True).start()
    ready.wait()


init()
