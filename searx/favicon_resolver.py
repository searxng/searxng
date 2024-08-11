# SPDX-License-Identifier: AGPL-3.0-or-later
"""This module implements functions needed for the favicon resolver.

"""
# pylint: disable=use-dict-literal

from httpx import HTTPError

from searx import settings

from searx.network import get as http_get, post as http_post
from searx.exceptions import SearxEngineResponseException


def update_kwargs(**kwargs):
    if 'timeout' not in kwargs:
        kwargs['timeout'] = settings['outgoing']['request_timeout']
    kwargs['raise_for_httperror'] = False


def get(*args, **kwargs):
    update_kwargs(**kwargs)
    return http_get(*args, **kwargs)


def post(*args, **kwargs):
    update_kwargs(**kwargs)
    return http_post(*args, **kwargs)


def allesedv(domain):
    """Favicon Resolver from allesedv.com"""

    url = 'https://f1.allesedv.com/32/{domain}'

    # will just return a 200 regardless of the favicon existing or not
    # sometimes will be correct size, sometimes not
    response = get(url.format(domain=domain))

    # returns image/gif if the favicon does not exist
    if response.headers['Content-Type'] == 'image/gif':
        return []

    return response.content


def duckduckgo(domain):
    """Favicon Resolver from duckduckgo.com"""

    url = 'https://icons.duckduckgo.com/ip2/{domain}.ico'

    # will return a 404 if the favicon does not exist and a 200 if it does,
    response = get(url.format(domain=domain))

    # api will respond with a 32x32 png image
    if response.status_code == 200:
        return response.content
    return []


def google(domain):
    """Favicon Resolver from google.com"""

    url = 'https://www.google.com/s2/favicons?sz=32&domain={domain}'

    # will return a 404 if the favicon does not exist and a 200 if it does,
    response = get(url.format(domain=domain))

    # api will respond with a 32x32 png image
    if response.status_code == 200:
        return response.content
    return []


def yandex(domain):
    """Favicon Resolver from yandex.com"""

    url = 'https://favicon.yandex.net/favicon/{domain}'

    # will always return 200
    response = get(url.format(domain=domain))

    # api will respond with a 16x16 png image, if it doesn't exist, it will be a 1x1 png image (70 bytes)
    if response.status_code == 200:
        if len(response.content) > 70:
            return response.content
    return []


backends = {
    'allesedv': allesedv,
    'duckduckgo': duckduckgo,
    'google': google,
    'yandex': yandex,
}


def search_favicon(backend_name, domain):
    backend = backends.get(backend_name)
    if backend is None:
        return []
    try:
        return backend(domain)
    except (HTTPError, SearxEngineResponseException):
        return []
