# SPDX-License-Identifier: AGPL-3.0-or-later
"""Keenable is a fast web search with keyless mode support"""

import typing as t

from datetime import datetime
from searx.extended_types import SXNG_Response
from searx.result_types import EngineResults
from searx.utils import searxng_useragent

if t.TYPE_CHECKING:
    from searx.search.processors import OnlineParams

about = {
    "website": "https://keenable.ai",
    "official_api_documentation": "https://docs.keenable.ai",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}
api_key = ""
""" Optional API Key. You can create a key at `the official website
<https://keenable.ai/signup>'_ if you need higher rate limits."""

categories = ["general"]

base_url = "https://api.keenable.ai"
keenable_mode = "pro"


def request(query: str, params: "OnlineParams"):
    if api_key:
        params["url"] = f"{base_url}/v1/search"
        params["headers"]["X-API-KEY"] = api_key
    else:
        params["url"] = f"{base_url}/v1/search/public"

    params["method"] = "POST"
    params["headers"]["X-Keenable-Title"] = searxng_useragent()
    params["json"] = {"query": query, "mode": keenable_mode}


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()

    results: list[dict[str, str]] = resp.json()["results"]  # type: ignore[reportAny]

    for result in results:
        published = None
        pub = result.get("published_at")
        if pub:
            try:
                published = datetime.fromisoformat(pub.rstrip("Z"))
            except ValueError:
                pass

        res.add(
            res.types.MainResult(
                url=result["url"], title=result["title"], content=result["description"], publishedDate=published
            )
        )

    return res
