# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Seekr (images, videos, news)
"""

from datetime import datetime
from json import loads
from urllib.parse import urlencode

about = {
    "website": 'https://seekr.com/',
    "official_api_documentation": None,
    "use_official_api": True,
    "require_api_key": True,
    "results": 'JSON',
}
paging = True  # news search doesn't support paging

base_url = "https://api.seekr.com"
# v2/newssearch, v1/imagetab, v1/videotab
seekr_path = "newssearch"
seekr_api_version = "v2"
api_key = "srh1-22fb-sekr"
results_per_page = 10


def request(query, params):
    args = {
        'query': query,
        'apiKey': api_key,
        'limit': results_per_page,
        'offset': (params['pageno'] - 1) * results_per_page,
    }

    path = f"{seekr_api_version}/{seekr_path}"
    if seekr_api_version == "v1":
        path = seekr_path

    params['url'] = f"{base_url}/engine/{path}?{urlencode(args)}"

    return params


def _images_response(json):
    results = []

    for result in json['expertResponses'][0]['advice']['results']:
        summary = loads(result['summary'])
        results.append(
            {
                'template': 'images.html',
                'url': summary['refererurl'],
                'title': result['title'],
                'img_src': result['url'],
                'img_format': f"{summary['width']}x{summary['height']}",
            }
        )

    return results


def _videos_response(json):
    results = []

    for result in json['expertResponses'][0]['advice']['results']:
        results.append(
            {
                'template': 'videos.html',
                'url': result['url'],
                'title': result['title'],
            }
        )

    return results


def _news_response(json):
    results = []

    for result in json['expertResponses'][0]['advice']['categorySearchResult']['searchResult']['results']:
        results.append(
            {
                'url': result['url'],
                'title': result['title'],
                'content': result['summary'],
                'thumbnail': result.get('thumbnail', ''),
                'publishedDate': datetime.strptime(result['pubDate'][:19], '%Y-%m-%d %H:%M:%S'),
            }
        )

    return results


def response(resp):
    json = resp.json()

    if seekr_path == "videotab":
        return _videos_response(json)
    if seekr_path == "imagetab":
        return _images_response(json)
    if seekr_path == "newssearch":
        return _news_response(json)

    raise ValueError(f"Unsupported seekr path: {seekr_path}")
