# SPDX-License-Identifier: AGPL-3.0-or-later
"""XPrivo"""

import json
import typing as t

from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": 'https://www.xprivo.com',
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ["general"]
paging = True
time_range_support = True

base_url = "https://www.xprivo.com"
page_size = 10  # not configurable

api_key = "API_KEY_XPRIVO"

XPrivoSearchType = t.Literal["all", "news", "videos"]
xprivo_search_type: XPrivoSearchType = "all"


def setup(_):
    if xprivo_search_type not in t.get_args(XPrivoSearchType):
        raise ValueError("invalid search type: %s" % {xprivo_search_type})


def request(query: str, params: "OnlineParams"):
    params["url"] = f"{base_url}/v1/searchengine/completions"
    params["headers"].update({"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})

    params["method"] = "POST"
    params["json"] = {
        "query": query,
        "mode": "classic",
        "search_type": xprivo_search_type,
        "time_filter": params["time_range"],
        "region": "",
        "offset": (params["pageno"] - 1) * page_size,
        "source": "",
    }


def response(resp: "SXNG_Response"):
    res = EngineResults()

    # response is a Server-Side Events (SSE) stream
    data_raw = resp.text.split("\n", 1)[0].removeprefix("data: ")
    data = json.loads(data_raw)

    for result in data["results"]:
        if xprivo_search_type == "videos":
            res.add(
                res.types.LegacyResult(
                    template="videos.html",
                    url=result["url"],
                    title=result["title"],
                    content=result["snippet"],
                    thumbnail=result.get("og_image"),
                )
            )
        else:
            res.add(
                res.types.MainResult(
                    url=result["url"],
                    title=result["title"],
                    content=result["snippet"],
                    thumbnail=result.get("og_image"),
                )
            )

    return res
