# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""MediathekViewWeb (API)

"""

import datetime
from json import loads, dumps

about = {
    "website": 'https://mediathekviewweb.de/',
    "wikidata_id": 'Q27877380',
    "official_api_documentation": 'https://gist.github.com/bagbag/a2888478d27de0e989cf777f81fb33de',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
    "language": "de",
}

categories = ['videos']
paging = True
time_range_support = False
safesearch = False


def request(query, params):

    params['url'] = 'https://mediathekviewweb.de/api/query'
    params['method'] = 'POST'
    params['headers']['Content-type'] = 'text/plain'
    params['data'] = dumps(
        {
            'queries': [
                {
                    'fields': [
                        'title',
                        'topic',
                    ],
                    'query': query,
                },
            ],
            'sortBy': 'timestamp',
            'sortOrder': 'desc',
            'future': True,
            'offset': (params['pageno'] - 1) * 10,
            'size': 10,
        }
    )
    return params


def response(resp):

    resp = loads(resp.text)

    mwv_result = resp['result']
    mwv_result_list = mwv_result['results']

    results = []

    for item in mwv_result_list:

        item['hms'] = str(datetime.timedelta(seconds=item['duration']))

        results.append(
            {
                'url': item['url_video_hd'].replace("http://", "https://"),
                'title': "%(channel)s: %(title)s (%(hms)s)" % item,
                'length': item['hms'],
                'content': "%(description)s" % item,
                'iframe_src': item['url_video_hd'].replace("http://", "https://"),
                'template': 'videos.html',
            }
        )

    return results
