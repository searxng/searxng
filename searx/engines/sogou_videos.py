# SPDX-License-Identifier: AGPL-3.0-or-later
"""Sogou-Videos: A search engine for retrieving videos from Sogou."""

from urllib.parse import urlencode
from datetime import datetime, timedelta

from searx.exceptions import SearxEngineAPIException

about = {
    "website": "https://v.sogou.com/",
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

categories = ["videos"]
paging = True
results_per_page = 10

# Base URL
base_url = "https://v.sogou.com"


def request(query, params):
    query_params = {
        "page": params["pageno"],
        "pagesize": 10,
        "query": query,
    }

    params["url"] = f"{base_url}/api/video/shortVideoV2?{urlencode(query_params)}"
    return params


def response(resp):
    try:
        data = resp.json()
    except Exception as e:
        raise SearxEngineAPIException(f"Invalid response: {e}") from e
    results = []

    if not data.get("data", {}).get("list"):
        raise SearxEngineAPIException("Invalid response")

    for entry in data["data"]["list"]:
        if not entry.get("titleEsc") or not entry.get("url"):
            continue

        video_url = entry.get("url")
        if video_url.startswith("/vc/np"):
            video_url = f"{base_url}{video_url}"

        published_date = None
        if entry.get("date") and entry.get("duration"):
            try:
                published_date = datetime.strptime(entry['date'], "%Y-%m-%d")
            except (ValueError, TypeError):
                published_date = None

        length = None
        if entry.get("date") and entry.get("duration"):
            try:
                timediff = datetime.strptime(entry['duration'], "%M:%S")
                length = timedelta(minutes=timediff.minute, seconds=timediff.second)
            except (ValueError, TypeError):
                length = None

        results.append(
            {
                'url': video_url,
                'title': entry["titleEsc"],
                'content': entry['site'],
                'length': length,
                'template': 'videos.html',
                'publishedDate': published_date,
                'thumbnail': entry["picurl"],
            }
        )

    return results
