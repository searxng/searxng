# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""
    Apple App Store
"""

from json import loads
from urllib.parse import urlencode
from dateutil.parser import parse

about = {
    "website": 'https://www.apple.com/app-store/',
    "wikidata_id": 'Q368215',
    "official_api_documentation": (
        'https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/'
        'iTuneSearchAPI/UnderstandingSearchResults.html#//apple_ref/doc/uid/TP40017632-CH8-SW1'
    ),
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ['files', 'apps']
safesearch = True

search_url = 'https://itunes.apple.com/search?{query}'


def request(query, params):
    explicit = "Yes"

    if params['safesearch'] > 0:
        explicit = "No"

    params['url'] = search_url.format(query=urlencode({'term': query, 'media': 'software', 'explicit': explicit}))

    return params


def response(resp):
    results = []

    json_result = loads(resp.text)

    for result in json_result['results']:
        results.append(
            {
                'url': result['trackViewUrl'],
                'title': result['trackName'],
                'content': result['description'],
                'img_src': result['artworkUrl100'],
                'publishedDate': parse(result['currentVersionReleaseDate']),
                'author': result['sellerName'],
            }
        )

    return results
