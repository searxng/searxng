# SPDX-License-Identifier: AGPL-3.0-or-later
"""Yep (general, images, news)
"""

from datetime import datetime
from urllib.parse import urlencode
from searx.utils import html_to_text

about = {
    'website': 'https://yep.com/',
    'official_api_documentation': 'https://docs.developer.yelp.com',
    'use_official_api': False,
    'require_api_key': False,
    'results': 'JSON',
}

base_url = "https://api.yep.com"
search_type = "web"  # 'web', 'images', 'news'

safesearch = True
safesearch_map = {0: 'off', 1: 'moderate', 2: 'strict'}


def request(query, params):
    args = {
        'client': 'web',
        'no_correct': 'false',
        'q': query,
        'safeSearch': safesearch_map[params['safesearch']],
        'type': search_type,
    }
    params['url'] = f"{base_url}/fs/2/search?{urlencode(args)}"
    params['headers']['Referer'] = 'https://yep.com/'
    return params


def _web_result(result):
    return {
        'url': result['url'],
        'title': result['title'],
        'content': html_to_text(result['snippet']),
    }


def _images_result(result):
    return {
        'template': 'images.html',
        'url': result['host_page'],
        'title': result.get('title', ''),
        'content': '',
        'img_src': result['image_id'],
        'thumbnail_src': result['src'],
    }


def _news_result(result):
    return {
        'url': result['url'],
        'title': result['title'],
        'content': html_to_text(result['snippet']),
        'publishedDate': datetime.strptime(result['first_seen'][:19], '%Y-%m-%dT%H:%M:%S'),
    }


def response(resp):
    results = []

    for result in resp.json()[1]['results']:
        if search_type == "web":
            results.append(_web_result(result))
        elif search_type == "images":
            results.append(_images_result(result))
        elif search_type == "news":
            results.append(_news_result(result))
        else:
            raise ValueError(f"Unsupported yep search type: {search_type}")

    return results
