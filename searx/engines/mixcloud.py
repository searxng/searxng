# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Mixcloud (Music)

"""

from urllib.parse import urlencode
from dateutil import parser

# about
about = {
    "website": 'https://www.mixcloud.com/',
    "wikidata_id": 'Q6883832',
    "official_api_documentation": 'http://www.mixcloud.com/developers/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ['music']
paging = True

# search-url
url = 'https://api.mixcloud.com/'
search_url = url + 'search/?{query}&type=cloudcast&limit=10&offset={offset}'
iframe_src = "https://www.mixcloud.com/widget/iframe/?feed={url}"


def request(query, params):
    offset = (params['pageno'] - 1) * 10
    params['url'] = search_url.format(query=urlencode({'q': query}), offset=offset)
    return params


def response(resp):
    results = []
    search_res = resp.json()

    for result in search_res.get('data', []):

        r_url = result['url']
        publishedDate = parser.parse(result['created_time'])
        res = {
            'url': r_url,
            'title': result['name'],
            'iframe_src': iframe_src.format(url=r_url),
            'img_src': result['pictures']['medium'],
            'publishedDate': publishedDate,
            'content': result['user']['name'],
        }
        results.append(res)

    return results
