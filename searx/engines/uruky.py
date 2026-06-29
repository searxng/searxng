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

if t.TYPE_CHECKING:
    from searx.search.processors import OnlineParams
    from searx.extended_types import SXNG_Response

about = {
    "website": "https://uruky.com",
    "official_api_documentation": "https://uruky.com/faq",
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
}

api_key = ""
uruky_categ: t.Literal["search", "images"] = "search"
"""Available categories: "search", "images"."""
uruky_providers = []
categories = ["general", "web"]
paging = True
safesearch = True
time_range_support = True

base_url = "https://uruky.com"

categ_paths = {
    "search": "/search",
    "images": "/image-search",
}

safe_search_map = {0: "0", 1: "1", 2: "1"}
time_range_map = {"day": "d", "week": "w", "month": "m", "year": "y"}


def init(_):
    if not api_key:
        raise ValueError("api_key is required for uruky")
    if uruky_categ not in categ_paths:
        raise ValueError(f"unsupported uruky_categ: {uruky_categ}")


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

    params["url"] = f"{base_url}{categ_paths[uruky_categ]}?{urlencode(args)}"


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()
    if uruky_categ == "search":
        for r in resp.json().get("results", []):
            res.add(
                res.types.MainResult(
                    url=r["url"],
                    title=r["title"],
                    content=r.get("description", ""),
                )
            )
    elif uruky_categ == "images":
        for r in resp.json().get("results", []):
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
