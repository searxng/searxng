# SPDX-License-Identifier: AGPL-3.0-or-later
"""MediathekViewWeb (API)"""

import typing as t
import datetime

from searx.result_types import EngineResults
from searx.utils import parse_duration_string

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://mediathekviewweb.de/",
    "wikidata_id": "Q27877380",
    "official_api_documentation": "https://gist.github.com/bagbag/a2888478d27de0e989cf777f81fb33de",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

language = "de"
categories = ["videos"]
paging = True
time_range_support = False
safesearch = False


def request(query: str, params: "OnlineParams"):

    params["url"] = "https://mediathekviewweb.de/api/query"
    params["method"] = "POST"
    params["headers"]["Content-type"] = "text/plain"
    params["json"] = {
        "queries": [
            {
                "fields": [
                    "title",
                    "topic",
                    "description",
                ],
                "query": query,
            },
        ],
        "sortBy": "timestamp",
        "sortOrder": "desc",
        "future": True,
        "offset": (params["pageno"] - 1) * 10,
        "size": 10,
    }


def response(resp: "SXNG_Response") -> EngineResults:

    json_resp: dict[str, t.Any] = resp.json()

    mwv_result = json_resp["result"]
    mwv_result_list = mwv_result["results"]

    res = EngineResults()

    for item in mwv_result_list:
        item["hms"] = str(datetime.timedelta(seconds=item["duration"]))

        video_url = item["url_video_hd"] or item["url_video"] or item["url_video_low"] or item["url_video"]
        if not video_url:
            continue

        res.add(
            res.types.Video(
                url=video_url,
                title="%(channel)s: %(title)s (%(hms)s)" % item,
                length=parse_duration_string(item["hms"]),
                content="%(description)s" % item,
                iframe_src=video_url,
            )
        )

    return res
