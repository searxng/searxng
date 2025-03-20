# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bilibili is a Chinese video sharing website.

.. _Bilibili: https://www.bilibili.com
"""

import random
import string
from urllib.parse import urlencode
from datetime import datetime, timedelta

from searx import utils

# Engine metadata
about = {
    "website": "https://www.bilibili.com",
    "wikidata_id": "Q3077586",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

# Engine configuration
paging = True
results_per_page = 20
categories = ["videos"]

# Search URL
base_url = "https://api.bilibili.com/x/web-interface/search/type"

cookie = {
    "innersign": "0",
    "buvid3": "".join(random.choice(string.hexdigits) for _ in range(16)) + "infoc",
    "i-wanna-go-back": "-1",
    "b_ut": "7",
    "FEED_LIVE_VERSION": "V8",
    "header_theme_version": "undefined",
    "home_feed_column": "4",
}


def request(query, params):
    query_params = {
        "__refresh__": "true",
        "page": params["pageno"],
        "page_size": results_per_page,
        "single_column": "0",
        "keyword": query,
        "search_type": "video",
    }

    params["url"] = f"{base_url}?{urlencode(query_params)}"
    params["cookies"] = cookie

    return params


def response(resp):
    search_res = resp.json()

    results = []

    for item in search_res.get("data", {}).get("result", []):
        title = utils.html_to_text(item["title"])
        url = item["arcurl"]
        thumbnail = item["pic"]
        description = item["description"]
        author = item["author"]
        video_id = item["aid"]
        unix_date = item["pubdate"]

        formatted_date = datetime.fromtimestamp(unix_date)

        # the duration only seems to be valid if the video is less than 60 mins
        duration = utils.parse_duration_string(item["duration"])
        if duration and duration > timedelta(minutes=60):
            duration = None

        iframe_url = f"https://player.bilibili.com/player.html?aid={video_id}&high_quality=1&autoplay=false&danmaku=0"

        results.append(
            {
                "title": title,
                "url": url,
                "content": description,
                "author": author,
                "publishedDate": formatted_date,
                "length": duration,
                "thumbnail": thumbnail,
                "iframe_src": iframe_url,
                "template": "videos.html",
            }
        )

    return results
