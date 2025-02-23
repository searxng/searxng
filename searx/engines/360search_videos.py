# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=invalid-name
"""360Search-Videos: A search engine for retrieving videos from 360Search."""

from urllib.parse import urlencode
from datetime import datetime

from searx.exceptions import SearxEngineAPIException
from searx.utils import html_to_text

about = {
    "website": "https://tv.360kan.com/",
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

paging = True
results_per_page = 10
categories = ["videos"]

base_url = "https://tv.360kan.com"


def request(query, params):
    query_params = {"count": 10, "q": query, "start": params["pageno"] * 10}

    params["url"] = f"{base_url}/v1/video/list?{urlencode(query_params)}"
    return params


def response(resp):
    try:
        data = resp.json()
    except Exception as e:
        raise SearxEngineAPIException(f"Invalid response: {e}") from e
    results = []

    if "data" not in data or "result" not in data["data"]:
        raise SearxEngineAPIException("Invalid response")

    for entry in data["data"]["result"]:
        if not entry.get("title") or not entry.get("play_url"):
            continue

        published_date = None
        if entry.get("publish_time"):
            try:
                published_date = datetime.fromtimestamp(int(entry["publish_time"]))
            except (ValueError, TypeError):
                published_date = None

        results.append(
            {
                'url': entry["play_url"],
                'title': html_to_text(entry["title"]),
                'content': html_to_text(entry["description"]),
                'template': 'videos.html',
                'publishedDate': published_date,
                'thumbnail': entry["cover_img"],
            }
        )

    return results
