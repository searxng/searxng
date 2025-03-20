# SPDX-License-Identifier: AGPL-3.0-or-later
"""iQiyi: A search engine for retrieving videos from iQiyi."""

from urllib.parse import urlencode
from datetime import datetime

from searx.exceptions import SearxEngineAPIException
from searx.utils import parse_duration_string

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

        length = parse_duration_string(album_info.get("subscriptionContent"))
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
