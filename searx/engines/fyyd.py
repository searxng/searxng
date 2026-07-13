# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fyyd (podcasts)"""

import typing as t

from datetime import datetime
from urllib.parse import urlencode

from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://fyyd.de",
    "official_api_documentation": "https://github.com/eazyliving/fyyd-api",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}
categories = []
paging = True

base_url = "https://api.fyyd.de"
page_size = 10


def request(query: str, params: "OnlineParams") -> None:
    args = {
        "term": query,
        "count": page_size,
        "page": params["pageno"] - 1,
    }
    params["url"] = f"{base_url}/0.2/search/podcast?{urlencode(args)}"


def response(resp: "SXNG_Response"):
    res = EngineResults()

    json_results: list[dict[str, str]] = resp.json()["data"]  # pyright: ignore[reportAny]

    for result in json_results:
        res.add(
            res.types.MainResult(
                url=result["htmlURL"],
                title=result["title"],
                content=result["description"],
                thumbnail=result["smallImageURL"],
                publishedDate=datetime.fromisoformat(result["status_since"]),
                metadata=f"Rank: {result['rank']} || {result['episode_count']} episodes",
            )
        )

    return res
