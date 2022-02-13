# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Mixcloud (Music)
"""

from json import loads
from dateutil import parser
from urllib.parse import urlencode

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

# do search-request
def request(query, params):
    offset = (params['pageno'] - 1) * 10

    params['url'] = search_url.format(query=urlencode({'q': query}), offset=offset)

    return params


# get response from search-request
def response(resp):
    results = []

    search_res = loads(resp.text)

    # parse results
    for result in search_res.get('data', []):
        title = result['name']
        url = result['url']
        content = result['user']['name']
        publishedDate = parser.parse(result['created_time'])

        # append result
        results.append(
            {
                'url': url,
                'title': title,
                'iframe_src': iframe_src.format(url=url),
                'publishedDate': publishedDate,
                'content': content,
            }
        )

    # return results
    return results
