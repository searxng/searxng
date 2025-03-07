# SPDX-License-Identifier: AGPL-3.0-or-later
"""ChinaSo: A search engine from ChinaSo."""

from urllib.parse import urlencode
from datetime import datetime

from searx.exceptions import SearxEngineAPIException
from searx.utils import html_to_text

about = {
    "website": "https://www.chinaso.com/",
    "wikidata_id": "Q10846064",
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
    "language": "zh",
}

paging = True
time_range_support = True
results_per_page = 10
categories = []
chinaso_category = 'news'
"""ChinaSo supports news, videos, images search.

- ``news``: search for news
- ``videos``: search for videos
- ``images``: search for images
"""

time_range_dict = {'day': '24h', 'week': '1w', 'month': '1m', 'year': '1y'}

base_url = "https://www.chinaso.com"


def init(_):
    if chinaso_category not in ('news', 'videos', 'images'):
        raise SearxEngineAPIException(f"Unsupported category: {chinaso_category}")


def request(query, params):
    query_params = {"q": query}

    if time_range_dict.get(params['time_range']):
        query_params["stime"] = time_range_dict[params['time_range']]
        query_params["etime"] = 'now'

    category_config = {
        'news': {'endpoint': '/v5/general/v1/web/search', 'params': {'pn': params["pageno"], 'ps': results_per_page}},
        'images': {
            'endpoint': '/v5/general/v1/search/image',
            'params': {'start_index': (params["pageno"] - 1) * results_per_page, 'rn': results_per_page},
        },
        'videos': {
            'endpoint': '/v5/general/v1/search/video',
            'params': {'start_index': (params["pageno"] - 1) * results_per_page, 'rn': results_per_page},
        },
    }

    query_params.update(category_config[chinaso_category]['params'])

    params["url"] = f"{base_url}{category_config[chinaso_category]['endpoint']}?{urlencode(query_params)}"

    return params


def response(resp):
    try:
        data = resp.json()
    except Exception as e:
        raise SearxEngineAPIException(f"Invalid response: {e}") from e

    parsers = {'news': parse_news, 'images': parse_images, 'videos': parse_videos}

    return parsers[chinaso_category](data)


def parse_news(data):
    results = []
    if not data.get("data", {}).get("data"):
        raise SearxEngineAPIException("Invalid response")

    for entry in data["data"]["data"]:
        published_date = None
        if entry.get("timestamp"):
            try:
                published_date = datetime.fromtimestamp(int(entry["timestamp"]))
            except (ValueError, TypeError):
                pass

        results.append(
            {
                'title': html_to_text(entry["title"]),
                'url': entry["url"],
                'content': html_to_text(entry["snippet"]),
                'publishedDate': published_date,
            }
        )
    return results


def parse_images(data):
    results = []
    if not data.get("data", {}).get("arrRes"):
        raise SearxEngineAPIException("Invalid response")

    for entry in data["data"]["arrRes"]:
        results.append(
            {
                'url': entry["web_url"],
                'title': html_to_text(entry["title"]),
                'content': html_to_text(entry["ImageInfo"]),
                'template': 'images.html',
                'img_src': entry["url"].replace("http://", "https://"),
                'thumbnail_src': entry["largeimage"].replace("http://", "https://"),
            }
        )
    return results


def parse_videos(data):
    results = []
    if not data.get("data", {}).get("arrRes"):
        raise SearxEngineAPIException("Invalid response")

    for entry in data["data"]["arrRes"]:
        published_date = None
        if entry.get("VideoPubDate"):
            try:
                published_date = datetime.fromtimestamp(int(entry["VideoPubDate"]))
            except (ValueError, TypeError):
                pass

        results.append(
            {
                'url': entry["url"],
                'title': html_to_text(entry["raw_title"]),
                'template': 'videos.html',
                'publishedDate': published_date,
                'thumbnail': entry["image_src"].replace("http://", "https://"),
            }
        )
    return results
