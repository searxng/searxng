# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Stack Exchange API v2.3

* https://api.stackexchange.com/

"""

import html
from json import loads
from urllib.parse import urlencode

about = {
    "website": 'https://stackexchange.com',
    "wikidata_id": 'Q3495447',
    "official_api_documentation": 'https://api.stackexchange.com/docs',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

paging = True
pagesize = 10

api_site = 'stackoverflow'
api_sort = 'activity'
api_order = 'desc'

# https://api.stackexchange.com/docs/advanced-search
search_api = 'https://api.stackexchange.com/2.3/search/advanced?'


def request(query, params):

    args = urlencode(
        {
            'q': query,
            'page': params['pageno'],
            'pagesize': pagesize,
            'site': api_site,
            'sort': api_sort,
            'order': 'desc',
        }
    )
    params['url'] = search_api + args

    return params


def response(resp):

    results = []
    json_data = loads(resp.text)

    for result in json_data['items']:

        content = "[%s]" % ", ".join(result['tags'])
        content += " %s" % result['owner']['display_name']
        if result['is_answered']:
            content += ' // is answered'
        content += " // score: %s" % result['score']

        results.append(
            {
                'url': "https://%s.com/q/%s" % (api_site, result['question_id']),
                'title': html.unescape(result['title']),
                'content': html.unescape(content),
            }
        )

    return results
