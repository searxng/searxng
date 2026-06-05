# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=invalid-name
"""Swisscows news"""

from datetime import datetime
from urllib.parse import urlencode

import typing as t

from searx.utils import html_to_text
from searx.result_types import EngineResults
from searx.engines.swisscows import appropriate_locale

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

swisscows_regions: list[str] = ["DE"]
"""Regions supported by swisscows News."""


def request(query: str, params: "OnlineParams") -> None:

    sxng_locale = params["searxng_locale"].split("-", maxsplit=1)[0]
    locale: str = appropriate_locale(sxng_locale, swisscows_regions, default="de-DE")
    if not locale:
        return

    freshness = "All"
    if params["time_range"]:
        freshness = time_range_map[params["time_range"]]

    args = {
        "query": query,
        "itemsCount": results_per_page,
        "region": locale,
        "language": locale.split("-", maxsplit=1)[0],
        "offset": (params["pageno"] - 1) * results_per_page,
        "freshness": freshness,
        "sortOrder": "Desc",
        "sortBy": "Created",
    }
    url_path = f"/news/search?{urlencode(args)}"

    params["url"] = base_url + url_path


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()

    result: dict[str, str]
    for result in resp.json()["items"]:  # pyright: ignore[reportAny]
        res.add(
            res.types.MainResult(
                url=result["uri"],
                title=html_to_text(result["title"]),
                content=result["description"],
                publishedDate=datetime.fromisoformat(result["created"]),
                thumbnail=result.get("og:image") or "",
            )
        )

    return res
