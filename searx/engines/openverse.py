# SPDX-License-Identifier: AGPL-3.0-or-later
"""Openverse (formerly known as: Creative Commons search engine) [Images]

As of 09/2026: The availability of https://openverse.org/ is poor, and queries
and image requests often time out. However, these issues also occur when using a
WEB browser to search on openverse.org or view images.
"""

import typing as t
from urllib.parse import urlencode
from dateutil import parser

from searx.result_types import EngineResults


if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://openverse.org/",
    "wikidata_id": None,
    "official_api_documentation": "https://api.openverse.org/v1/",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

categories = ["images"]

paging = True
page_size = 20

base_url = "https://api.openverse.org/v1/images/"


def request(query: str, params: "OnlineParams"):
    args: dict[str, str | int] = {
        "q": query,
        "page": params["pageno"],
        "page_size": page_size,
        "format": "json",
    }
    params["url"] = f"{base_url}?{urlencode(args)}"


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()
    json_data = resp.json()  # type: ignore

    for result in json_data["results"]:  # pyright: ignore[reportUnknownVariableType]
        res.add(
            res.types.Image(
                url=result["foreign_landing_url"],
                title=result["title"],
                img_src=result["url"],
                thumbnail_src=result["thumbnail"],
                resolution=f"{result['width']} x {result['height']}",
                author=result["creator"],
                publishedDate=parser.parse(result["indexed_on"]),
            )
        )
    return res
