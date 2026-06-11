# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fireball_ is a Germany-based, privacy-focused search engine.

It likely doesn't have its own index, but it's unclear where its results come
from.

.. _Fireball: https://fireball.com
"""

import typing as t

from datetime import datetime
from urllib.parse import urlencode

from searx.enginelib import EngineCache
from searx.exceptions import SearxEngineAPIException
from searx.extended_types import SXNG_Response

from searx.result_types import EngineResults
from searx.network import post
from searx.utils import html_to_text

if t.TYPE_CHECKING:
    from searx.search.processors import OnlineParams

about = {
    "website": "https://fireball.com",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

base_url = "https://fireball.com"
categories = ["general"]
fireball_category = "web"  # values: "web", "news", "videos"

paging = False
safesearch = True

safe_search_map = {0: "off", 1: "moderate", 2: "strict"}

CACHE: EngineCache
"""Cache to store the settings cookie (contains e.g. language, safesearch, ...)."""

CACHE_VALID_DURATION = 30 * 24 * 3600  # one month, same as website
"""Duration how long settings cookies are valid."""


def init(engine_settings: dict[str, t.Any]):
    global CACHE  # pylint: disable=global-statement
    CACHE = EngineCache(engine_settings["name"])

    if fireball_category not in ("web", "news", "videos"):
        raise ValueError(f"Unsupported category: {fireball_category}")


def _cache_key(fireball_settings: dict[str, str]) -> str:
    return f"fireball_settings_{fireball_settings['safesearch']}_{fireball_settings['market']}"


def _get_search_settings_cookie(params: 'OnlineParams') -> str:
    """Get a 'fireball' cookie for the given locale and safesearch setting set
    in params."""

    # the language is set by only specifying the search country on their
    # website, they only list DE and US, but in fact it supports much more
    # countries
    country = "US"
    if params["searxng_locale"] != "all":
        language_parts = params["searxng_locale"].split("-")
        country = language_parts[-1].upper()

    fireball_settings = {
        "action": "save",
        "language": "en",  # language is irrelevant, only changes UI language
        "market": country,
        "adprovider": "automatic",
        "target": "_blank",
        "tiles": "on",
        "safesearch": safe_search_map[params["safesearch"]],
    }
    cache_key = _cache_key(fireball_settings)

    cached_cookie = CACHE.get(cache_key)
    if cached_cookie:
        return cached_cookie

    resp = post("https://fireball.com/settings", data=fireball_settings)
    if not resp.ok:
        raise SearxEngineAPIException("failed to obtain cookie for settings")

    cookie = resp.cookies.get("fireball")
    if not cookie:
        raise SearxEngineAPIException("failed to obtain cookie for settings")

    CACHE.set(cache_key, cookie, expire=CACHE_VALID_DURATION)
    return cookie


def request(query: str, params: "OnlineParams"):
    # no matter the category, the request is always the same, i.e. we get all
    # different categories with one HTTP request

    args = {
        "f": "web",
        "q": query,
    }

    params["url"] = f"{base_url}/getResults/?{urlencode(args)}"
    params["cookies"]["fireball"] = _get_search_settings_cookie(params)

    # referer header has to be set, otherwise the requests get blocked
    params["headers"]["Referer"] = f"{base_url}/search?{urlencode(args)}"


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()

    json_data = resp.json()

    for result in json_data.get(fireball_category, {}).get("results", []):
        published_date = None
        if result.get("page_age"):
            published_date = datetime.fromisoformat(result["page_age"])

        if fireball_category == "web":
            res.add(
                res.types.MainResult(
                    url=result["url"],
                    title=html_to_text(result["title"]),
                    content=html_to_text(result["description"]),
                    publishedDate=published_date,
                )
            )
        elif fireball_category == "news":
            thumbnail: str | None = None
            if result.get("thumbnail"):
                thumbnail = result["thumbnail"]["src"]

            res.add(
                res.types.MainResult(
                    url=result["url"],
                    title=html_to_text(result["title"]),
                    content=html_to_text(result["description"]),
                    thumbnail=thumbnail or "",
                    publishedDate=published_date,
                )
            )
        elif fireball_category == "videos":
            length = None
            if result.get("video"):
                length = result["video"].get("duration")

            res.add(
                res.types.LegacyResult(
                    {
                        "template": "videos.html",
                        "url": result["url"],
                        "title": html_to_text(result["title"]),
                        "content": html_to_text(result["description"]),
                        "thumbnail": result.get("thumbnail", {}).get("original"),
                        "length": length,
                        "publishedDate": published_date,
                    }
                )
            )

    return res
