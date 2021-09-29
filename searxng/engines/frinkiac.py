# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Frinkiac (Images)
"""

from json import loads
from urllib.parse import urlencode

# about
about = {
    "website": 'https://frinkiac.com',
    "wikidata_id": 'Q24882614',
    "official_api_documentation": {
        'url': None,
        'comment': 'see https://github.com/MitchellAW/CompuGlobal'
    },
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ['images']

BASE = 'https://frinkiac.com/'
SEARCH_URL = '{base}api/search?{query}'
RESULT_URL = '{base}?{query}'
THUMB_URL = '{base}img/{episode}/{timestamp}/medium.jpg'
IMAGE_URL = '{base}img/{episode}/{timestamp}.jpg'


def request(query, params):
    params['url'] = SEARCH_URL.format(base=BASE, query=urlencode({'q': query}))
    return params


def response(resp):
    results = []
    response_data = loads(resp.text)
    for result in response_data:
        episode = result['Episode']
        timestamp = result['Timestamp']

        results.append({'template': 'images.html',
                        'url': RESULT_URL.format(base=BASE,
                                                 query=urlencode({'p': 'caption', 'e': episode, 't': timestamp})),
                        'title': episode,
                        'content': '',
                        'thumbnail_src': THUMB_URL.format(base=BASE, episode=episode, timestamp=timestamp),
                        'img_src': IMAGE_URL.format(base=BASE, episode=episode, timestamp=timestamp)})

    return results
