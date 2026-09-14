# SPDX-License-Identifier: AGPL-3.0-or-later
"""Uruky_ is an EU-based, privacy-focused meta search engine.

.. _Uruky : https://uruky.com

.. code:: yaml

  - name: uruky
    engine: uruky
    shortcut: ur
    categories: [general, web]
    api_key: ""
    uruky_providers: []    # default: mojeek,eusp,linkup,marginalia,serper,prieco

  - name: uruky.images
    engine: uruky
    shortcut: uri
    categories: [images]
    uruky_categ: images
    api_key: ""
    uruky_providers: []    # default: pixabay,serper
"""

import typing as t
from urllib.parse import urlencode

from searx.result_types import EngineResults
from searx.exceptions import SearxEngineAccessDeniedException

if t.TYPE_CHECKING:
    from searx.search.processors import OnlineParams
    from searx.extended_types import SXNG_Response

about = {
    "website": "https://uruky.com",
    "official_api_documentation": "https://uruky.com/faq",
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
    "description": (
        "Uruky is a EU-based, private search engine, free from ads and tracking,"
        " with a focus on search personalization, not AI or side-products."
    ),
}

api_key = ""
categories = None
paging = True
safesearch = True
time_range_support = True

base_url = "https://uruky.com"
safe_search_map = {0: "0", 1: "1", 2: "1"}
time_range_map = {"day": "d", "week": "w", "month": "m", "year": "y"}

uruky_categ: "UrukyCategory" = None  # type: ignore
uruky_providers: "list[UrukyProvider]" = []
"""List of providers, the defaults are (:py:obj:`URUKY_CATEGORIES`):

- ``search``: mojeek, eusp, linkup, marginalia, serper, prieco
- ``images``: pixabay, serper
"""

UrukyCategory: t.TypeAlias = t.Literal["search", "images"]
UrukyProvider: t.TypeAlias = t.Literal[
    "mojeek",
    "eusp",
    "linkup",
    "marginalia",
    "serper",
    "prieco",
    "pixabay",
    "serper",
]

CATEG_PATHS = {
    "search": "/search",
    "images": "/image-search",
}

URUKY_CATEGORIES: tuple[UrukyCategory] = t.get_args(UrukyCategory)
"""Available categories."""

URUKY_PROVIDERS: tuple[UrukyProvider] = t.get_args(UrukyProvider)
"""Available providers."""


def setup(_):
    if not api_key:
        raise ValueError("api_key is required for uruky")
    if uruky_categ not in URUKY_CATEGORIES:
        raise ValueError(f"unsupported uruky_categ: {uruky_categ}")
    for provider in uruky_providers:
        if provider not in URUKY_PROVIDERS:
            raise ValueError(f"unsupported provider in uruky_providers: {provider}")
    return True


def request(query: str, params: "OnlineParams"):
    args = {
        "q": query,
        "i": api_key,
        "f": "json",
        "p": params["pageno"],
        "s": safe_search_map[params["safesearch"]],
    }

    locale = params.get("searxng_locale", "all")
    if locale != "all":
        parts = locale.split("-")
        args["l"] = parts[0].upper()
        if len(parts) > 1:
            args["c"] = parts[1].upper()

    if params["time_range"]:
        args["w"] = time_range_map[params["time_range"]]

    if uruky_providers:
        args["sp"] = ",".join(uruky_providers)

    params["method"] = "GET"
    params["url"] = f"{base_url}{CATEG_PATHS[uruky_categ]}?{urlencode(args)}"


def response(resp: "SXNG_Response") -> EngineResults:

    if resp.status_code == 302:
        # migth a problem with the login
        raise SearxEngineAccessDeniedException(message=f"HTTP 302 {resp.text}: {resp.headers['location'][:30]}...")

    res = EngineResults()
    items: list[dict[str, str]] = resp.json().get("results", [])  # type: ignore

    if uruky_categ == "search":
        for r in items:
            res.add(
                res.types.MainResult(
                    url=r["url"],
                    title=r["title"],
                    content=r.get("description", ""),
                )
            )

    elif uruky_categ == "images":
        for r in items:
            res.add(
                res.types.Image(
                    url=r["sourceUrl"],
                    title=r.get("title", ""),
                    img_src=base_url + r["imageUrl"],
                    thumbnail_src=base_url + r["thumbnailUrl"],
                    resolution=f"{r['width']}x{r['height']}",
                )
            )
    return res
