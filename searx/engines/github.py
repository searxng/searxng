# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Github (IT)
"""

from json import loads
from urllib.parse import urlencode

# about
about = {
    "website": 'https://github.com/',
    "wikidata_id": 'Q364',
    "official_api_documentation": 'https://developer.github.com/v3/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ['it', 'repos']

# search-url
search_url = 'https://api.github.com/search/repositories?sort=stars&order=desc&{query}'  # noqa

accept_header = 'application/vnd.github.preview.text-match+json'


# do search-request
def request(query, params):
    params['url'] = search_url.format(query=urlencode({'q': query}))

    params['headers']['Accept'] = accept_header

    return params


# get response from search-request
def response(resp):
    results = []

    search_res = loads(resp.text)

    # check if items are received
    if 'items' not in search_res:
        return []

    # parse results
    for res in search_res['items']:
        title = res['name']
        url = res['html_url']

        if res['description']:
            content = res['description'][:500]
        else:
            content = ''

        # append result
        results.append({'url': url, 'title': title, 'content': content})

    # return results
    return results
