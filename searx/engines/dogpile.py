# SPDX-License-Identifier: AGPL-3.0-or-later
"""Dogpile is a metasearch engine by the American advertising company `System1`_.

.. _System1: https://system1.com/
"""

import typing as t
from datetime import datetime, timezone
import html

from searx.utils import format_duration, html_to_text, humanize_number
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://www.dogpile.com",
    "wikidata_id": "Q3595363",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

paging = True
safesearch = True

categories = ["general"]
dogpile_categ = "search"
"""Category to search in. Can be either "search", "images", "videos" or "news"."""


base_url = "https://www.dogpile.com"
safe_search_map = {0: "none", 1: "moderate", 2: "heavy"}


def init(_):
    if dogpile_categ not in ("search", "images", "videos", "news"):
        raise ValueError("invalid search type: %s" % dogpile_categ)


def request(query: str, params: "OnlineParams"):
    params["url"] = f"{base_url}/api/{dogpile_categ}"
    params["method"] = "POST"
    params["json"] = {"q": query, "qadf": safe_search_map[params["safesearch"]], "page": params["pageno"]}
    return params


def response(resp: "SXNG_Response"):
    res = EngineResults()

    json_resp = resp.json()

    for result in json_resp["results"]:
        if dogpile_categ == "search":
            res.add(
                res.types.MainResult(
                    url=result["clickUrl"],
                    title=html_to_text(result["title"]),
                    content=html_to_text(result["description"]),
                )
            )
        elif dogpile_categ == "news":
            res.add(
                res.types.MainResult(
                    url=result["clickUrl"],
                    title=html_to_text(html.unescape(result["title"])),
                    content=html_to_text(html.unescape(result["description"])),
                    thumbnail=result["thumbnailUrl"],
                    publishedDate=datetime.fromtimestamp(result["date"], tz=timezone.utc),
                )
            )
        elif dogpile_categ == "videos":
            res.add(
                res.types.LegacyResult(
                    template="videos.html",
                    url=result["clickUrl"],
                    title=html_to_text(result["title"]),
                    content=html_to_text(result["description"]),
                    thumbnail=result["thumbnailUrl"],
                    publishedDate=datetime.fromisoformat(result["publishDate"]),
                    length=format_duration(result["duration"]),
                    views=humanize_number(result["viewCount"]),
                )
            )
        elif dogpile_categ == "images":
            res.add(
                res.types.Image(
                    url=result["altClickUrl"],
                    title=html_to_text(result["title"]),
                    content=html_to_text(result["description"]),
                    img_src=result["clickUrl"],
                    thumbnail_src=result["thumbnailUrl"],
                    resolution=f"{result['width']}x{result['height']}",
                    img_format=result["format"],
                )
            )

    return res
