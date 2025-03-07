# SPDX-License-Identifier: AGPL-3.0-or-later
"""iQiyi: A search engine for retrieving videos from iQiyi."""

from urllib.parse import urlencode
from datetime import datetime, timedelta

from searx.exceptions import SearxEngineAPIException

about = {
    "website": "https://www.iqiyi.com/",
    "wikidata_id": "Q15913890",
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
    "language": "zh",
}

paging = True
time_range_support = True
categories = ["videos"]

time_range_dict = {'day': '1', 'week': '2', 'month': '3'}

base_url = "https://mesh.if.iqiyi.com"


def request(query, params):
    query_params = {"key": query, "pageNum": params["pageno"], "pageSize": 25}

    if time_range_dict.get(params['time_range']):
        query_params["sitePublishDate"] = time_range_dict[params['time_range']]

    params["url"] = f"{base_url}/portal/lw/search/homePageV3?{urlencode(query_params)}"
    return params


def response(resp):
    try:
        data = resp.json()
    except Exception as e:
        raise SearxEngineAPIException(f"Invalid response: {e}") from e
    results = []

    if "data" not in data or "templates" not in data["data"]:
        raise SearxEngineAPIException("Invalid response")

    for entry in data["data"]["templates"]:
        album_info = entry.get("albumInfo", {})

        published_date = None
        release_time = album_info.get("releaseTime", {}).get("value")
        if release_time:
            try:
                published_date = datetime.strptime(release_time, "%Y-%m-%d")
            except (ValueError, TypeError):
                pass

        length = None
        subscript_content = album_info.get("subscriptContent")
        if subscript_content:
            try:
                time_parts = subscript_content.split(":")
                if len(time_parts) == 2:
                    minutes, seconds = map(int, time_parts)
                    length = timedelta(minutes=minutes, seconds=seconds)
                elif len(time_parts) == 3:
                    hours, minutes, seconds = map(int, time_parts)
                    length = timedelta(hours=hours, minutes=minutes, seconds=seconds)
            except (ValueError, TypeError):
                pass

        results.append(
            {
                'url': album_info.get("pageUrl", "").replace("http://", "https://"),
                'title': album_info.get("title", ""),
                'content': album_info.get("brief", {}).get("value", ""),
                'template': 'videos.html',
                'length': length,
                'publishedDate': published_date,
                'thumbnail': album_info.get("img", ""),
            }
        )

    return results
