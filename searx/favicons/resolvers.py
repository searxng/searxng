# SPDX-License-Identifier: AGPL-3.0-or-later
"""Implementations of the favicon *resolvers* that are available in the favicon
proxy by default.  A *resolver* is a function that obtains the favicon from an
external source.  The *resolver* function receives two arguments (``domain,
timeout``) and returns a tuple ``(data, mime)``.

"""

from __future__ import annotations

__all__ = ["DEFAULT_RESOLVER_MAP", "allesedv", "duckduckgo", "google", "yandex"]

from typing import Callable
from searx import network
from searx import logger

DEFAULT_RESOLVER_MAP: dict[str, Callable]
logger = logger.getChild('favicons.resolvers')


def _req_args(**kwargs):
    # add the request arguments from the searx.network
    d = {"raise_for_httperror": False}
    d.update(kwargs)
    return d


def allesedv(domain: str, timeout: int) -> tuple[None | bytes, None | str]:
    """Favicon Resolver from allesedv.com / https://favicon.allesedv.com/"""
    data, mime = (None, None)
    url = f"https://f1.allesedv.com/32/{domain}"
    logger.debug("fetch favicon from: %s", url)

    # will just return a 200 regardless of the favicon existing or not
    # sometimes will be correct size, sometimes not
    response = network.get(url, **_req_args(timeout=timeout))
    if response and response.status_code == 200:
        mime = response.headers['Content-Type']
        if mime != 'image/gif':
            data = response.content
    return data, mime


def duckduckgo(domain: str, timeout: int) -> tuple[None | bytes, None | str]:
    """Favicon Resolver from duckduckgo.com / https://blog.jim-nielsen.com/2021/displaying-favicons-for-any-domain/"""
    data, mime = (None, None)
    url = f"https://icons.duckduckgo.com/ip2/{domain}.ico"
    logger.debug("fetch favicon from: %s", url)

    # will return a 404 if the favicon does not exist and a 200 if it does,
    response = network.get(url, **_req_args(timeout=timeout))
    if response and response.status_code == 200:
        # api will respond with a 32x32 png image
        mime = response.headers['Content-Type']
        data = response.content
    return data, mime


def google(domain: str, timeout: int) -> tuple[None | bytes, None | str]:
    """Favicon Resolver from google.com"""
    data, mime = (None, None)

    # URL https://www.google.com/s2/favicons?sz=32&domain={domain}" will be
    # redirected (HTTP 301 Moved Permanently) to t1.gstatic.com/faviconV2:
    url = (
        f"https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL"
        f"&url=https://{domain}&size=32"
    )
    logger.debug("fetch favicon from: %s", url)

    # will return a 404 if the favicon does not exist and a 200 if it does,
    response = network.get(url, **_req_args(timeout=timeout))
    if response and response.status_code == 200:
        # api will respond with a 32x32 png image
        mime = response.headers['Content-Type']
        data = response.content
    return data, mime


def yandex(domain: str, timeout: int) -> tuple[None | bytes, None | str]:
    """Favicon Resolver from yandex.com"""
    data, mime = (None, None)
    url = f"https://favicon.yandex.net/favicon/{domain}"
    logger.debug("fetch favicon from: %s", url)

    # api will respond with a 16x16 png image, if it doesn't exist, it will be a
    # 1x1 png image (70 bytes)
    response = network.get(url, **_req_args(timeout=timeout))
    if response and response.status_code == 200 and len(response.content) > 70:
        mime = response.headers['Content-Type']
        data = response.content
    return data, mime


DEFAULT_RESOLVER_MAP = {
    "allesedv": allesedv,
    "duckduckgo": duckduckgo,
    "google": google,
    "yandex": yandex,
}
