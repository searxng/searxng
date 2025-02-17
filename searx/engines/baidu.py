# SPDX-License-Identifier: AGPL-3.0-or-later
"""Baidu

.. Website: https://www.baidu.com
"""

from urllib.parse import urlencode
from datetime import datetime

from searx.exceptions import SearxEngineAPIException

about = {
    "website": "https://www.baidu.com",
    "wikidata_id": "Q14772",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

paging = True
results_per_page = 10
categories = ["general"]

base_url = "https://www.baidu.com/s"


def request(query, params):
    keyword = query.strip()

    query_params = {"wd": keyword, "rn": 20, "pn": params["pageno"], "tn": "json"}

    params["url"] = f"{base_url}?{urlencode(query_params)}"
    return params


def response(resp):
    data = resp.json()
    results = []

    entries = data.get("feed", {}).get("entry")
    if not entries:
        raise SearxEngineAPIException("Invalid response")
    for entry in entries:
        if not entry.get("title") or not entry.get("url"):
            continue

        published_date = None
        if entry.get("time"):
            try:
                published_date = datetime.fromtimestamp(entry["time"])
            except (ValueError, TypeError):
                published_date = None

        results.append(
            {
                "title": entry["title"],
                "url": entry["url"],
                "content": entry.get("abs", ""),
                "publishedDate": published_date,
            }
        )

    return results
