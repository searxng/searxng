# SPDX-License-Identifier: AGPL-3.0-or-later
"""Baidu-Kaifa: A search engine for retrieving coding / development from Baidu."""

from urllib.parse import urlencode

import time

from searx.exceptions import SearxEngineAPIException

about = {
    "website": "https://kaifa.baidu.com/",
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

paging = True
time_range_support = True
results_per_page = 10
categories = ["it"]

time_range_dict = {"day": 86400, "week": 604800, "month": 2592000, "year": 31536000}

base_url = "https://kaifa.baidu.com"


def request(query, params):
    page_num = params["pageno"]

    query_params = {
        "wd": query,
        "paramList": f"page_num={page_num},page_size={results_per_page}",
        "pageNum": page_num,
        "pageSize": results_per_page,
        "position": 0,
    }

    if params.get("time_range") in time_range_dict:
        now = int(time.time())
        past = now - time_range_dict[params["time_range"]]
        query_params["paramList"] += f",timestamp_range={past}-{now}"

    params["url"] = f"{base_url}/rest/v1/search?{urlencode(query_params)}"
    return params


def response(resp):
    try:
        data = resp.json()
    except Exception as e:
        raise SearxEngineAPIException(f"Invalid response: {e}") from e

    results = []

    if not data.get("data", {}).get("documents", {}).get("data"):
        raise SearxEngineAPIException("Invalid response")

    for entry in data["data"]["documents"]["data"]:
        results.append(
            {
                'title': entry["techDocDigest"]["title"],
                'url': entry["techDocDigest"]["url"],
                'content': entry["techDocDigest"]["summary"],
            }
        )

    return results
