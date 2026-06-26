# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bilibili is a Chinese video sharing website.

.. _Bilibili: https://www.bilibili.com
"""

import random
import string
from urllib.parse import urlencode
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

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

_CN_TZ = ZoneInfo("Asia/Shanghai")

# Calendar-day time filter (Asia/Shanghai); dict values are days to subtract from today.
time_range_support = True
time_range_dict = {"day": 0, "week": 6, "month": 29, "year": 364}


def _pubtime_range(time_range: str) -> tuple[int, int]:
    """Return ``(pubtime_begin_s, pubtime_end_s)`` for Bilibili's search API.

    Time ranges follow Bilibili's website semantics: they are counted in
    **calendar days** in China Standard Time (``Asia/Shanghai``), not as
    sliding 24-hour windows.  For example, ``day`` means from 00:00:00 to
    23:59:59 of the current local day; ``week`` spans from 00:00:00 on the
    calendar day six days ago through the end of today, and so on.

    The returned Unix timestamps (seconds) map to Bilibili's
    ``pubtime_begin_s`` and ``pubtime_end_s`` query parameters.
    """
    now = datetime.now(_CN_TZ)
    pubtime_end_s = int(now.replace(hour=23, minute=59, second=59, microsecond=0).timestamp())
    begin_day = now - timedelta(days=time_range_dict[time_range])
    pubtime_begin_s = int(begin_day.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())

    return pubtime_begin_s, pubtime_end_s


def request(query, params):
    query_params = {
        "__refresh__": "true",
        "page": params["pageno"],
        "page_size": results_per_page,
        "single_column": "0",
        "keyword": query,
        "search_type": "video",
    }

    if params.get("time_range") in time_range_dict:
        pubtime_begin_s, pubtime_end_s = _pubtime_range(params["time_range"])
        query_params["pubtime_begin_s"] = pubtime_begin_s
        query_params["pubtime_end_s"] = pubtime_end_s

    params["url"] = f"{base_url}?{urlencode(query_params)}"
    params["headers"]["Referer"] = "https://www.bilibili.com/"
    params["headers"]["Accept"] = "application/json, text/javascript, */*; q=0.01"
    params["cookies"] = cookie


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
