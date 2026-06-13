# SPDX-License-Identifier: AGPL-3.0-or-later
"""DuckDuckGo Web (general)

This implementation fetches the link to the first API page
(i.e. ``links.duckduckgo.com/d.js?...``) from duckduckgo.com and uses the ``n``
parameter of the API to fetch all subsequent pages.

This also means that it's not possible to immediately search for the third
page - the first and the second page would need to be loaded first.

The reason why we can't just normally use the `vqd` value is that the API URLs
require an additional parameter `dp` which seems generated at server-side, so we
can't build it ourselves and must scrape it from the HTML pages.
"""

import typing as t

from urllib.parse import quote_plus
from lxml import html

from searx.utils import html_to_text, gen_useragent, extract_text, eval_xpath
from searx.result_types import EngineResults
from searx.enginelib import EngineCache
from searx.network import get

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://duckduckgo.com/",
    "wikidata_id": "Q12805",
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

# engine dependent config
categories = ["general"]
paging = True
_HTTP_User_Agent: str = gen_useragent()

base_url = "https://duckduckgo.com"

CACHE: EngineCache
"""Cache to store the API URLs for combinations of (query, page)."""


def setup(engine_settings: dict[str, str]):
    global CACHE  # pylint:disable=global-statement
    CACHE = EngineCache(engine_settings["name"])
    return CACHE


def _fetch_first_page_link(
    query: str,
    headers: dict[str, str],
):
    """Search for a::

        <link id="deep_preload_link" rel="preload" as="script"
              href="https://links.duckduckgo.com/d.js?q=rust&t=D&l=us-en&s=0&a=h_&ct=DE&vqd=VQD_VALUE&bing_market=en-US&p_ent=&ex=-1&dp=LONG_TOKEN
        >

    This points to the first page
    """  # pylint:disable=line-too-long

    cache_key = _cache_key(query, 1)
    cached: str | None = CACHE.get(cache_key)
    if cached:
        return cached

    resp = get(
        url=f"{base_url}/?q={quote_plus(query)}&t=h_&ia=web",
        headers=headers,
        timeout=2,
    )

    if resp.status_code != 200:
        logger.error("vqd: got HTTP %s from duckduckgo.com", resp.status_code)

    dom = html.fromstring(resp.text)
    first_page_link = extract_text(eval_xpath(dom, "//link[@id='deep_preload_link']/@href"))

    if not first_page_link:
        logger.error("vqd: failed to load first page JS url from ddg response (return empty string)")
        return ""

    logger.debug("got link to first page from duckduckgo.com request: '%s'", first_page_link)
    CACHE.set(cache_key, first_page_link, expire=7200)

    return first_page_link


def _cache_key(query: str, pageno: int) -> str:
    return f"nextpage_url|{query}|{pageno}"


def request(query: str, params: "OnlineParams") -> None:

    if len(query) >= 500:
        # DDG does not accept queries with more than 499 chars
        params["url"] = None
        return

    headers = params["headers"]

    # The vqd value is generated from the query and the UA header.  To be able
    # to reuse the vqd value, the UA header must be static.
    headers["User-Agent"] = _HTTP_User_Agent
    headers["Accept"] = "*/*"
    headers["Referer"] = f"{base_url}/"
    headers["Host"] = "duckduckgo.com"

    # Sec-Fetch headers are required to not get blocked when sending a Firefox user agent
    headers["Sec-Fetch-Dest"] = "script"
    headers["Sec-Fetch-Mode"] = "no-cors"
    headers["Sec-Fetch-Site"] = "same-site"

    api_url = ""
    if params["pageno"] > 1:
        api_url = CACHE.get(_cache_key(query, params["pageno"]))
    else:
        api_url = _fetch_first_page_link(query, headers)

    if not api_url:
        params["url"] = None
        return

    params["url"] = api_url.replace("/d.js?", "/d.js?o=json&")

    # TODO: support safesearch, timerange and engine traits  # pylint:disable=fixme


def response(resp: "SXNG_Response"):
    res = EngineResults()
    res_json = resp.json()

    for result in res_json["results"]:
        if "u" not in result:
            continue

        res.add(
            res.types.MainResult(url=result["u"], title=html_to_text(result["t"]), content=html_to_text(result["a"]))
        )

    # link to next page
    next_page_path = res_json["results"][-1].get("n")
    if next_page_path:
        CACHE.set(
            _cache_key(resp.search_params["query"], resp.search_params["pageno"] + 1),
            base_url + next_page_path,
            expire=60 * 60,
        )

    return res
