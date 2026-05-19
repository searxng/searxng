# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=invalid-name
"""Swisscows news"""

from datetime import datetime
from urllib.parse import urlencode

import typing as t

from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://swisscows.com",
    "wikidata_id": "Q22937452",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}


categories = ["news"]
results_per_page = 20

time_range_support = True
paging = True

base_url = "https://api.swisscows.com"
time_range_map = {"day": "Day", "week": "Week", "month": "Month", "year": "Year"}


def request(query: str, params: "OnlineParams") -> None:
    freshness = "All"
    if params["time_range"]:
        freshness = time_range_map[params["time_range"]]

    args = {
        "query": query,
        "itemsCount": results_per_page,
        "region": "de-DE",
        "language": "de",
        "offset": (params["pageno"] - 1) * results_per_page,
        "freshness": freshness,
        "sortOrder": "Desc",
        "sortBy": "Created",
    }
    url_path = f"/news/search?{urlencode(args)}"

    params["url"] = base_url + url_path


def response(resp: "SXNG_Response"):
    res = EngineResults()

    for result in resp.json()["items"]:
        res.add(
            res.types.MainResult(
                url=result["uri"],
                title=result["title"],
                content=result["description"],
                publishedDate=datetime.fromisoformat(result["created"]),
                thumbnail=result.get("og:image"),
            )
        )

    return res
