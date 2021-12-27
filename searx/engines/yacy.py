# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Yacy (Web, Images, Videos, Music, Files)
"""

from json import loads
from dateutil import parser
from urllib.parse import urlencode

from httpx import DigestAuth

from searx.utils import html_to_text

# about
about = {
    "website": 'https://yacy.net/',
    "wikidata_id": 'Q1759675',
    "official_api_documentation": 'https://wiki.yacy.net/index.php/Dev:API',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ['general', 'images']  # TODO , 'music', 'videos', 'files'
paging = True
number_of_results = 5
http_digest_auth_user = ""
http_digest_auth_pass = ""

# search-url
base_url = 'http://localhost:8090'
search_url = (
    '/yacysearch.json?{query}'
    '&startRecord={offset}'
    '&maximumRecords={limit}'
    '&contentdom={search_type}'
    '&resource=global'
)

# yacy specific type-definitions
search_types = {'general': 'text', 'images': 'image', 'files': 'app', 'music': 'audio', 'videos': 'video'}


# do search-request
def request(query, params):
    offset = (params['pageno'] - 1) * number_of_results
    search_type = search_types.get(params.get('category'), '0')

    params['url'] = base_url + search_url.format(
        query=urlencode({'query': query}), offset=offset, limit=number_of_results, search_type=search_type
    )

    if http_digest_auth_user and http_digest_auth_pass:
        params['auth'] = DigestAuth(http_digest_auth_user, http_digest_auth_pass)

    # add language tag if specified
    if params['language'] != 'all':
        params['url'] += '&lr=lang_' + params['language'].split('-')[0]

    return params


# get response from search-request
def response(resp):
    results = []

    raw_search_results = loads(resp.text)

    # return empty array if there are no results
    if not raw_search_results:
        return []

    search_results = raw_search_results.get('channels', [])

    if len(search_results) == 0:
        return []

    for result in search_results[0].get('items', []):
        # parse image results
        if resp.search_params.get('category') == 'images':

            result_url = ''
            if 'url' in result:
                result_url = result['url']
            elif 'link' in result:
                result_url = result['link']
            else:
                continue

            # append result
            results.append(
                {
                    'url': result_url,
                    'title': result['title'],
                    'content': '',
                    'img_src': result['image'],
                    'template': 'images.html',
                }
            )

        # parse general results
        else:
            publishedDate = parser.parse(result['pubDate'])

            # append result
            results.append(
                {
                    'url': result['link'],
                    'title': result['title'],
                    'content': html_to_text(result['description']),
                    'publishedDate': publishedDate,
                }
            )

        # TODO parse video, audio and file results

    return results
