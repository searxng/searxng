# SPDX-License-Identifier: AGPL-3.0-or-later
"""Baidu_

.. _Baidu: https://www.baidu.com
"""

# There exits a https://github.com/ohblue/baidu-serp-api/
# but we don't use it here (may we can learn from).

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
    "language": "zh",
}

paging = True
categories = ["general"]
base_url = "https://www.baidu.com/s"
results_per_page = 10


def request(query, params):
    keyword = query.strip()

    query_params = {
        "wd": keyword,
        "rn": results_per_page,
        "pn": (params["pageno"] - 1) * results_per_page,
        "tn": "json",
    }

    params["url"] = f"{base_url}?{urlencode(query_params)}"
    return params


def response(resp):
    try:
        data = resp.json()
    except Exception as e:
        raise SearxEngineAPIException(f"Invalid response: {e}") from e
    results = []

    if "feed" not in data or "entry" not in data["feed"]:
        raise SearxEngineAPIException("Invalid response")

    for entry in data["feed"]["entry"]:
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
                # "source": entry.get('source')
            }
        )

    return results
