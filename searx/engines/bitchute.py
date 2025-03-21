# SPDX-License-Identifier: AGPL-3.0-or-later
"""bitchute (Videos)"""

from json import dumps
from datetime import datetime
from searx.utils import html_to_text

about = {
    "website": 'https://bitchute.com',
    "wikidata_id": "Q45287179",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

base_url = "https://api.bitchute.com/api/beta/search/videos"
categories = ['videos']
paging = True
results_per_page = 20


def request(query, params):

    start_index = (params["pageno"] - 1) * results_per_page
    data = {"offset": start_index, "limit": results_per_page, "query": query, "sensitivity_id": "normal", "sort": "new"}
    params["url"] = base_url
    params["method"] = 'POST'
    params['headers']['content-type'] = "application/json"
    params['data'] = dumps(data)

    return params


def response(resp):
    search_res = resp.json()
    results = []

    for item in search_res.get('videos', []):

        results.append(
            {
                "title": item['video_name'],
                "url": 'https://www.bitchute.com/video/' + item['video_id'],
                "content": html_to_text(item['description']),
                "author": item['channel']['channel_name'],
                "publishedDate": datetime.strptime(item["date_published"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                "length": item['duration'],
                "views": item['view_count'],
                "thumbnail": item['thumbnail_url'],
                "iframe_src": 'https://www.bitchute.com/embed/' + item['video_id'],
                "template": "videos.html",
            }
        )

    return results
