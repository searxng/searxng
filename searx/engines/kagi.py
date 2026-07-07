# SPDX-License-Identifier: AGPL-3.0-or-later
"""Kagi_ is a paid, privacy-focused search engine.

Using it requires an API key. If you have a Kagi account, you can obtain an API
key in the `API portal`_.

To enable Kagi, add the following to the ``engines`` seciton of
``settings.yml``:

.. code:: yaml

  - name: kagi
    engine: kagi
    categories: [general, web]
    shortcut: kg
    api_key: ""
    kagi_categ: search

  - name: kagi.news
    engine: kagi
    categories: [news, web]
    shortcut: kgn
    api_key: ""
    kagi_categ: news

  - name: kagi.images
    engine: kagi
    categories: [images, web]
    shortcut: kgi
    paging: false
    api_key: ""
    kagi_categ: images

  - name: kagi.videos
    engine: kagi
    categories: [videos, web]
    shortcut: kgv
    api_key: ""
    kagi_categ: videos

.. _Kagi: https://kagi.com
.. _Api Portal: https://help.kagi.com/kagi/api/overview.html
"""

from datetime import datetime, timedelta

import typing as t


from searx.extended_types import SXNG_Response
from searx.result_types import EngineResults
from searx.utils import html_to_text, parse_duration_string

if t.TYPE_CHECKING:
    from searx.search.processors import OnlineParams

TimeRangeType = t.Literal["day", "week", "month", "year"]
about = {
    "website": "https://kagi.com",
    "wikidata_id": "Q26000117",
    "official_api_documentation": "https://kagi.com/api/docs/openapi",
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
}

paging = True
"""All categories except the ``images`` category support paging."""
safesearch = True
time_range_support = True

categories = ["general"]
kagi_categ: t.Literal["search", "images", "news", "videos"] = "search"
"""Search category. Supported values: "search" (general), "images", "news", "videos"."""

base_url = "https://kagi.com"

safe_search_map = {0: False, 1: True, 2: True}
time_range_to_days_map: dict[TimeRangeType, int] = {
    "day": 1,
    "week": 7,
    "month": 30,
    "year": 365,
}

api_key = ""
"""Kagi API key. Required for using this engine."""


def init(_):
    if not api_key:
        raise ValueError("api_key is required for using kagi")

    if kagi_categ not in ("search", "images", "news", "videos"):
        raise ValueError(f"Unsupported category: {kagi_categ}")  # pyright: ignore[reportUnreachable]


def request(query: str, params: "OnlineParams"):
    # According to the API docs, Kagi supports at maximum page 10
    if params["pageno"] > 10:
        return

    params["headers"]["Authorization"] = f"Bearer {api_key}"
    params["url"] = f"{base_url}/api/v1/search"

    filters = {}
    time_range = params.get("time_range")
    if time_range:
        # Kagi expects the minimum date to return results from as argument to `after`
        time_period = timedelta(days=time_range_to_days_map[time_range])
        oldest_result_date = datetime.now() - time_period
        filters["after"] = oldest_result_date.strftime("%Y-%m-%d")

    # there doesn't seem to be a list of languages anywhere,
    # so we just assume that it supports all languages

    filters["region"] = "no_region"
    if params["searxng_locale"] != "all":
        _locale = params["searxng_locale"].split("-")
        if len(_locale) > 1:
            filters["region"] = _locale[-1].lower()

    args: dict[str, t.Any] = {
        "query": query,
        "page": params["pageno"],
        "workflow": kagi_categ,
        "safe_search": safe_search_map[params["safesearch"]],
        "filters": filters,
    }

    params["method"] = "POST"
    params["json"] = args


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()

    json_data: dict[str, t.Any] = resp.json()

    if kagi_categ in ("images", "videos"):
        # the JSON key is "image" for "images" and "video" for "videos"
        json_results = json_data["data"].get(kagi_categ[:-1])
    else:
        json_results = json_data["data"].get(kagi_categ)

    # if no results were found, the response doesn't contain the results field
    if not json_results:
        return res

    for result in json_results:
        published_date: datetime | None = None
        if result.get("time"):
            published_date = datetime.fromisoformat(result["time"])

        if kagi_categ in ("search", "news"):
            res.add(
                res.types.MainResult(
                    url=result["url"],
                    title=html_to_text(result.get("title", "no title available")),
                    content=html_to_text(result.get("snippet", "")),
                    thumbnail=result.get("image", {}).get("url") or "",
                    publishedDate=published_date,
                )
            )
        elif kagi_categ == "images":
            res.add(
                res.types.Image(
                    url=result["url"],
                    title=html_to_text(result.get("title", "no title available")),
                    img_src=result.get("image", {}).get("url"),
                    resolution=f"{result.get('image', {}).get('width')}x{result.get('image', {}).get('height')}",
                    thumbnail_src=result.get("props", {}).get("thumbnail", {}).get("url"),
                )
            )
        elif kagi_categ == "videos":
            length: timedelta | None = None
            if result.get("props", {}).get("duration"):
                length = parse_duration_string(result["props"]["duration"])

            res.add(
                res.types.LegacyResult(
                    {
                        "template": "videos.html",
                        "url": result["url"],
                        "title": html_to_text(result.get("title", "no title available")),
                        "content": html_to_text(result.get("snippet", "")),
                        "thumbnail": result.get("image", {}).get("url"),
                        "publishedDate": published_date,
                        "author": result.get("props", {}).get("creator_name"),
                        "length": length,
                    }
                )
            )

    for suggestion in json_data["data"].get("related_search", []):
        res.add(res.types.LegacyResult({"suggestion": suggestion["title"]}))

    return res
