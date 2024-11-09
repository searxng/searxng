# SPDX-License-Identifier: AGPL-3.0-or-later
"""Adobe Stock (images)
"""

from urllib.parse import urlencode
from searx.utils import gen_useragent

about = {
    "website": 'https://stock.adobe.com/',
    "wikidata_id": 'Q5977430',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ['images']
paging = True

base_url = 'https://stock.adobe.com'

results_per_page = 10
adobe_order = "relevance"  # one of 'relevant', 'featured', 'creation' or 'nb_downloads'


def request(query, params):
    args = {
        'k': query,
        'limit': results_per_page,
        'order': adobe_order,
        'search_page': params['pageno'],
        'search_type': 'pagination',
        'filters[content_type:video]': 0,
        'filters[content_type:audio]': 0,
    }
    params['url'] = f"{base_url}/de/Ajax/Search?{urlencode(args)}"

    # headers required to bypass bot-detection
    params['headers'] = {
        "User-Agent": gen_useragent(),
        "Accept-Language": "en-US,en;q=0.5",
    }

    return params


def response(resp):
    results = []

    json_resp = resp.json()

    for item in json_resp['items'].values():
        results.append(
            {
                'template': 'images.html',
                'url': item['content_url'],
                'title': item['title'],
                'content': '',
                'img_src': item['content_thumb_extra_large_url'],
                'thumbnail_src': item['thumbnail_url'],
                'resolution': f"{item['content_original_width']}x{item['content_original_height']}",
                'img_format': item['format'],
                'author': item['author'],
            }
        )

    return results
