# SPDX-License-Identifier: AGPL-3.0-or-later
"""Findborg_ is a small search engine that gets its results from Brave.

.. _Findborg: https://www.findborg.com/about/
"""

import typing as t
from urllib.parse import urlencode

from searx.engines.brave import parse_images_json, parse_news_json, parse_videos_json, parse_web_json
from searx.extended_types import SXNG_Response
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.search.processors import OnlineParams

about = {
    "website": "https://www.findborg.com",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}
categories: list[str] = None  # type: ignore[reportAssignmentType]
time_range_support = True

FindborgCategType = t.Literal["search", "images", "videos", "news"]
findborg_categ: FindborgCategType = None  # type: ignore[reportAssignmentType]


base_url = "https://www.findborg.com"


def setup(_: dict[str, t.Any]):
    if findborg_categ not in t.get_args(FindborgCategType):
        raise ValueError("invalid category: %s" % findborg_categ)


def request(query: str, params: "OnlineParams"):
    args = {"q": query, "type": findborg_categ}
    if params["time_range"]:
        args["time"] = params["time_range"]
    params["url"] = f"{base_url}/apis/proxy.php?{urlencode(args)}"


def response(resp: "SXNG_Response") -> EngineResults:
    data: dict[str, t.Any] = resp.json()["data"]  # type: ignore[reportAny]

    match findborg_categ:
        case "search":
            return parse_web_json(data["web"]["results"])
        case "news":
            return parse_news_json(data["results"])
        case "videos":
            return parse_videos_json(data["results"])
        case "images":
            return parse_images_json(data["results"])
