# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reuters_ (news) is an international news agency.

.. _Reuters: https://www.reuters.com

Configuration
=============

The engine has the following additional settings:

- :py:obj:`sort_order`

.. code:: yaml

   - name: reuters
     engine: reuters
     shortcut: reu
     sort_order: "relevance"


Implementations
===============

"""

from json import dumps
from urllib.parse import quote_plus
from datetime import datetime, timedelta

from searx.result_types import EngineResults

about = {
    "website": "https://www.reuters.com",
    "wikidata_id": "Q130879",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

categories = ["news"]
time_range_support = True
paging = True

base_url = "https://www.reuters.com"

results_per_page = 20
sort_order = "relevance"
"""Sort order, one of ``relevance``, ``display_date:desc`` or ``display_data:asc``."""

time_range_duration_map = {
    "day": 1,
    "week": 7,
    "month": 30,
    "year": 365,
}


def request(query, params):
    args = {
        "keyword": query,
        "offset": (params["pageno"] - 1) * results_per_page,
        "orderby": sort_order,
        "size": results_per_page,
        "website": "reuters",
    }
    if params["time_range"]:
        time_diff_days = time_range_duration_map[params["time_range"]]
        start_date = datetime.now() - timedelta(days=time_diff_days)
        args["start_date"] = start_date.isoformat()

    params["url"] = f"{base_url}/pf/api/v3/content/fetch/articles-by-search-v2?query={quote_plus(dumps(args))}"
    return params


def response(resp) -> EngineResults:
    res = EngineResults()

    for result in resp.json().get("result", {}).get("articles", []):
        res.add(
            res.types.MainResult(
                url=base_url + result["canonical_url"],
                title=result["web"],
                content=result["description"],
                thumbnail=result.get("thumbnail", {}).get("url", ""),
                metadata=result.get("kicker", {}).get("name"),
                publishedDate=datetime.strptime(result["display_time"], "%Y-%m-%dT%H:%M:%SZ"),
            )
        )
    return res
