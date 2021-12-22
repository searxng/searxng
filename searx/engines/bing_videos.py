# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Bing (Videos)

"""

from json import loads
from urllib.parse import urlencode

from lxml import html

from searx.utils import match_language
from searx.engines.bing import language_aliases

from searx.engines.bing import (  # pylint: disable=unused-import
    _fetch_supported_languages,
    supported_languages_url,
)

about = {
    "website": 'https://www.bing.com/videos',
    "wikidata_id": 'Q4914152',
    "official_api_documentation": 'https://www.microsoft.com/en-us/bing/apis/bing-video-search-api',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['videos', 'web']
paging = True
safesearch = True
time_range_support = True
number_of_results = 28

base_url = 'https://www.bing.com/'
search_string = (
    # fmt: off
    'videos/search'
    '?{query}'
    '&count={count}'
    '&first={first}'
    '&scope=video'
    '&FORM=QBLH'
    # fmt: on
)
time_range_string = '&qft=+filterui:videoage-lt{interval}'
time_range_dict = {'day': '1440', 'week': '10080', 'month': '43200', 'year': '525600'}

# safesearch definitions
safesearch_types = {2: 'STRICT', 1: 'DEMOTE', 0: 'OFF'}


# do search-request
def request(query, params):
    offset = ((params['pageno'] - 1) * number_of_results) + 1

    search_path = search_string.format(query=urlencode({'q': query}), count=number_of_results, first=offset)

    # safesearch cookie
    params['cookies']['SRCHHPGUSR'] = 'ADLT=' + safesearch_types.get(params['safesearch'], 'DEMOTE')

    # language cookie
    language = match_language(params['language'], supported_languages, language_aliases).lower()
    params['cookies']['_EDGE_S'] = 'mkt=' + language + '&F=1'

    # query and paging
    params['url'] = base_url + search_path

    # time range
    if params['time_range'] in time_range_dict:
        params['url'] += time_range_string.format(interval=time_range_dict[params['time_range']])

    # bing videos did not like "older" versions < 70.0.1 when selectin other
    # languages then 'en' .. very strange ?!?!
    params['headers']['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64; rv:73.0.1) Gecko/20100101 Firefox/73.0.1'

    return params


# get response from search-request
def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    for result in dom.xpath('//div[@class="dg_u"]'):
        metadata = loads(result.xpath('.//div[@class="vrhdata"]/@vrhm')[0])
        info = ' - '.join(result.xpath('.//div[@class="mc_vtvc_meta_block"]//span/text()')).strip()
        content = '{0} - {1}'.format(metadata['du'], info)
        thumbnail = '{0}th?id={1}'.format(base_url, metadata['thid'])
        results.append(
            {
                'url': metadata['murl'],
                'thumbnail': thumbnail,
                'title': metadata.get('vt', ''),
                'content': content,
                'template': 'videos.html',
            }
        )

    return results
