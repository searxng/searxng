# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=invalid-name
"""360Search search engine for searxng"""

import typing as t

from urllib.parse import urlencode
from lxml import html

from searx import logger
from searx.enginelib import EngineCache
from searx.utils import extract_text
from searx.network import get as http_get

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response

# Metadata
about = {
    "website": "https://www.so.com/",
    "wikidata_id": "Q10846064",
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
    "language": "zh",
}

# Engine Configuration
categories = ["general"]
paging = True
time_range_support = True

time_range_dict = {'day': 'd', 'week': 'w', 'month': 'm', 'year': 'y'}

# Base URL
base_url = "https://www.so.com"
COOKIE_CACHE_KEY = "cookie"
COOKIE_CACHE_EXPIRATION_SECONDS = 3600

CACHE: EngineCache
"""Stores cookies from 360search to avoid re-fetching them on every request."""


def setup(engine_settings: dict[str, t.Any]) -> bool:
    """Initialization of the engine.

    - Instantiate a cache for this engine (:py:obj:`CACHE`).

    """
    global CACHE  # pylint: disable=global-statement
    # table name needs to be quoted to start with digits, so "cache" has been added to avoid sqlite complaining
    CACHE = EngineCache("cache" + engine_settings["name"])
    return True


def get_cookie(url: str) -> str:
    cookie: str | None = CACHE.get(COOKIE_CACHE_KEY)
    if cookie:
        return cookie
    resp: SXNG_Response = http_get(url, timeout=10, allow_redirects=False)
    headers = resp.headers
    cookie = headers['set-cookie'].split(";")[0]
    CACHE.set(key=COOKIE_CACHE_KEY, value=cookie, expire=COOKIE_CACHE_EXPIRATION_SECONDS)

    return cookie


def request(query, params):
    query_params = {
        "pn": params["pageno"],
        "q": query,
    }

    if time_range_dict.get(params['time_range']):
        query_params["adv_t"] = time_range_dict.get(params['time_range'])
    params["url"] = f"{base_url}/s?{urlencode(query_params)}"
    # get token by calling the query page
    logger.debug("querying url: %s", params["url"])
    cookie = get_cookie(params["url"])
    logger.debug("obtained cookie: %s", cookie)
    params['headers'] = {'Cookie': cookie}

    return params


def response(resp):
    dom = html.fromstring(resp.text)
    results = []

    for item in dom.xpath('//li[contains(@class, "res-list")]'):
        title = extract_text(item.xpath('.//h3[contains(@class, "res-title")]/a'))

        url = extract_text(item.xpath('.//h3[contains(@class, "res-title")]/a/@data-mdurl'))
        if not url:
            url = extract_text(item.xpath('.//h3[contains(@class, "res-title")]/a/@href'))

        content = extract_text(item.xpath('.//p[@class="res-desc"]'))
        if not content:
            content = extract_text(item.xpath('.//span[@class="res-list-summary"]'))

        if title and url:
            results.append(
                {
                    "title": title,
                    "url": url,
                    "content": content,
                }
            )

    return results
