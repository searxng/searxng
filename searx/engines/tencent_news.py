# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tencent-News: A search engine for retrieving news from Tencent."""

from urllib.parse import urlencode
import json
from datetime import datetime

from searx.exceptions import SearxEngineAPIException, SearxEngineTooManyRequestsException

# Metadata
about = {
    "website": "https://news.qq.com/",
    "wikidata_id": "Q47524073",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

# Engine Configuration
paging = True
results_per_page = 10
categories = ["news"]

base_url = "https://i.news.qq.com"


def request(query, params):
    query_params = {
        "page": params["pageno"],
        "query": query,
        "search_type": "all",
        "search_count_limit": results_per_page,
        "is_pc": 1,
    }

    params["url"] = f"{base_url}/gw/pc_search/result?{urlencode(query_params)}"
    return params


def response(resp):
    results = []

    try:
        data = resp.json()
    except json.JSONDecodeError as e:
        raise SearxEngineAPIException(f"Invalid JSON response: {e}") from e

    sec_list = data.get("secList")
    if not sec_list:
        raise SearxEngineTooManyRequestsException(
            suspended_time=0, message=f"Response is empty or rate-limited by {base_url}, secList not found in response."
        )

    for section in sec_list:
        news_list = section.get("newsList", [])
        for news in news_list:
            results.append(parse_news(news))

        videos_list = section.get("videoList", [])
        for video in videos_list:
            results.append(parse_news(video))

    return results


def parse_news(item):
    images = item.get("thumbnails_qqnews") or item.get("thumbnails_qqnews_photo") or []

    published_date = None
    timestamp = item.get("timestamp", "")
    if timestamp:
        published_date = datetime.fromtimestamp(int(timestamp))

    return {
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "content": item.get("abstract", ""),
        "thumbnail": images[0] if images else None,
        "publishedDate": published_date,
    }
