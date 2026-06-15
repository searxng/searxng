# SPDX-License-Identifier: AGPL-3.0-or-later
"""Startpagina is a Netherlands search engine by `Kompas`_. It takes all its
results from Google.

.. _Kompas: https://www.kompaspublishing.nl/
"""

import typing as t
from urllib.parse import urlencode

from dateutil import parser

from searx.utils import format_duration
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://startpagina.nl",
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

language = "ne"
paging = True
safesearch = True

categories = ["general"]
startpagina_categ = "web"
"""Category to search in. Can be either "web", "images", "videos" or "news"."""
page_size = 10


api_url = "https://search.kompas.services"


def init(_):
    if startpagina_categ not in ("web", "images", "videos", "news"):
        raise ValueError("invalid search type: %s" % startpagina_categ)


def request(query: str, params: "OnlineParams") -> None:
    args = {"q": query, "page_size": page_size, "page": params["pageno"]}
    params["url"] = f"{api_url}/api/v2/search/{startpagina_categ}/?{urlencode(args)}"


def response(resp: "SXNG_Response"):
    res = EngineResults()

    json_resp = resp.json()

    for result in json_resp["results"]:
        if startpagina_categ == "web":
            res.add(
                res.types.MainResult(
                    url=result["original_url"],
                    title=result["title"],
                    content=result["description"],
                )
            )
        elif startpagina_categ == "news":
            publishedDate = None
            try:
                publishedDate = parser.parse(result["date"])
            except parser.ParserError:
                pass

            res.add(
                res.types.MainResult(
                    url=result["original_url"],
                    title=result["title"],
                    content=result["description"],
                    thumbnail=result["image"]["thumbnail_url"],
                    publishedDate=publishedDate,
                )
            )
        elif startpagina_categ == "videos":
            res.add(
                res.types.LegacyResult(
                    template="videos.html",
                    url=result["original_url"],
                    title=result["title"],
                    content=result["description"],
                    thumbnail=result["video"]["thumbnail_url"],
                    length=format_duration(result["video"]["duration"]),
                )
            )
        elif startpagina_categ == "images":
            res.add(
                res.types.Image(
                    url=result["original_url"],
                    title=result["title"],
                    content=result["description"],
                    thumbnail_src=result["image"]["thumbnail_url"],
                    resolution=f"{result['image']['width']}x{result['image']['height']}",
                )
            )

    for related in json_resp["related_searches"]:
        res.add(res.types.LegacyResult(suggestion=related["query"]))

    return res
