# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 DuckDuckGo (Images)
"""

from json import loads
from urllib.parse import urlencode
from searx.exceptions import SearxEngineAPIException
from searx.engines.duckduckgo import get_region_code
from searx.engines.duckduckgo import (  # pylint: disable=unused-import
    _fetch_supported_languages,
    supported_languages_url,
)
from searx.network import get

# about
about = {
    "website": 'https://duckduckgo.com/',
    "wikidata_id": 'Q12805',
    "official_api_documentation": {
        'url': 'https://duckduckgo.com/api',
        'comment': 'but images are not supported',
    },
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON (site requires js to get images)',
}

# engine dependent config
categories = ['images', 'web']
paging = True
safesearch = True

# search-url
images_url = 'https://duckduckgo.com/i.js?{query}&s={offset}&p={safesearch}&o=json&vqd={vqd}'
site_url = 'https://duckduckgo.com/?{query}&iar=images&iax=1&ia=images'


# run query in site to get vqd number needed for requesting images
# TODO: find a way to get this number without an extra request (is it a hash of the query?)
def get_vqd(query, headers):
    query_url = site_url.format(query=urlencode({'q': query}))
    res = get(query_url, headers=headers)
    content = res.text
    if content.find('vqd=\'') == -1:
        raise SearxEngineAPIException('Request failed')
    vqd = content[content.find('vqd=\'') + 5 :]
    vqd = vqd[: vqd.find('\'')]
    return vqd


# do search-request
def request(query, params):
    # to avoid running actual external requests when testing
    if 'is_test' not in params:
        vqd = get_vqd(query, params['headers'])
    else:
        vqd = '12345'

    offset = (params['pageno'] - 1) * 50

    safesearch = params['safesearch'] - 1

    region_code = get_region_code(params['language'], lang_list=supported_languages)
    if region_code:
        params['url'] = images_url.format(
            query=urlencode({'q': query, 'l': region_code}), offset=offset, safesearch=safesearch, vqd=vqd
        )
    else:
        params['url'] = images_url.format(query=urlencode({'q': query}), offset=offset, safesearch=safesearch, vqd=vqd)

    return params


# get response from search-request
def response(resp):
    results = []

    content = resp.text
    res_json = loads(content)

    # parse results
    for result in res_json['results']:
        title = result['title']
        url = result['url']
        thumbnail = result['thumbnail']
        image = result['image']

        # append result
        results.append(
            {
                'template': 'images.html',
                'title': title,
                'content': '',
                'thumbnail_src': thumbnail,
                'img_src': image,
                'url': url,
            }
        )

    return results
