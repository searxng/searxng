# SPDX-License-Identifier: AGPL-3.0-or-later
"""Podchaser (podcasts)"""

import typing as t

from datetime import datetime
from urllib.parse import urlencode

from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://www.podchaser.com",
    "official_api_documentation": "https://www.podchaser.com/api",
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}
categories = []
paging = True

base_url = "https://api.podchaser.com"
page_size = 25


def request(query: str, params: "OnlineParams") -> None:
    args = {
        "filters[term]": query,
        "limit": page_size,
        "offset": (params["pageno"] - 1) * page_size,
        "sort_direction": "desc",
        "sort_order": "SORT_ORDER_RELEVANCE",
    }
    params["url"] = f"{base_url}/podcasts?{urlencode(args)}"
    params["headers"]["Accept"] = "application/prs.podchaser.v2+json"


def response(resp: "SXNG_Response"):
    res = EngineResults()

    json_results: list[dict[str, str]] = resp.json()["entities"]  # pyright: ignore[reportAny]

    for result in json_results:
        metadata = [f"{result['number_of_episodes']} episodes"]
        if result["categories"]:
            metadata.append(", ".join(c["text"] for c in result["categories"]))  # pyright: ignore[reportArgumentType]

        res.add(
            res.types.MainResult(
                url=result["feed_url"],
                title=result["title"],
                content=result["description"],
                thumbnail=result["image_url"],
                publishedDate=datetime.fromisoformat(result["created_at"]),
                metadata=" | ".join(metadata),
            )
        )

    return res
