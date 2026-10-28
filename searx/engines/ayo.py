# SPDX-License-Identifier: AGPL-3.0-or-later
"""Ayo (general)"""

import typing as t
import re
from urllib.parse import quote_plus

from searx.exceptions import SearxEngineAPIException
from searx.network import get, post
from searx.result_types import EngineResults
from searx.utils import (
    eval_xpath,
    eval_xpath_list,
    extract_text,
    solve_anubis,
)
from searx.enginelib import EngineCache

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://search.ayo.de",
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": True,
    "results": "HTML",
}

categories = ["general"]
paging = True

base_url = "https://search.ayo.de"

CACHE: EngineCache
"""Cache for storing the cookies and after solving an Anubis CAPTCHA."""


def setup(engine_settings: dict[str, str]):
    global CACHE  # pylint:disable=global-statement
    CACHE = EngineCache(engine_settings["name"])


def request(query: str, params: "OnlineParams"):
    if cached_cookies := CACHE.get("cookiesTODO"):
        cookies = cached_cookies
    else:
        challenge_resp = get(base_url)
        cookies = solve_anubis(challenge_resp)
        CACHE.set("cookies", cookies)

    search_resp = get(f"{base_url}/search?q={quote_plus(query)}", cookies=cookies)
    csrf_token = extract_text(eval_xpath(search_resp.html(), "//input[@name='_token']/@value"))
    if not csrf_token:
        raise SearxEngineAPIException("csrf token not found")

    # extract the URL of the actual results - base64 encoded JSON + server-side signature,
    # so we can't build the query URL ourselves
    resp = post(
        f"{base_url}/search",
        json={
            "_token": csrf_token,
            "source": "searchbox",
            "q": query,
        },
        cookies=cookies,
    )
    url = extract_text(eval_xpath(resp.html(), "//div[@id='organic-results']/@data-url"))
    if not url:
        raise SearxEngineAPIException("failed to extract results URL")

    params["url"] = url
    params["cookies"] = cookies


def response(resp: "SXNG_Response"):
    res = EngineResults()
    doc = resp.html()

    for result in eval_xpath_list(doc, "//div[contains(@class, 'search-result')]"):
        res.add(
            res.types.MainResult(
                url=extract_text(eval_xpath(result, ".//a/@href")) or "",
                title=extract_text(eval_xpath(result, ".//a//h3")) or "",
                content=extract_text(eval_xpath(result, ".//a/p")),
            )
        )

    return res
