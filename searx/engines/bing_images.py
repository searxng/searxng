# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Bing (Images)

"""

from json import loads
from urllib.parse import urlencode

from lxml import html

from searx.utils import match_language
from searx.enginelib.traits import EngineTraits

# about
about = {
    "website": 'https://www.bing.com/images',
    "wikidata_id": 'Q182496',
    "official_api_documentation": 'https://www.microsoft.com/en-us/bing/apis/bing-image-search-api',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['images', 'web']
paging = True
safesearch = True
time_range_support = True
send_accept_language_header = True
supported_languages_url = 'https://www.bing.com/account/general'
number_of_results = 28

# search-url
base_url = 'https://www.bing.com/'
search_string = (
    # fmt: off
    'images/search'
    '?{query}'
    '&count={count}'
    '&first={first}'
    '&tsc=ImageHoverTitle'
    # fmt: on
)
time_range_string = '&qft=+filterui:age-lt{interval}'
time_range_dict = {'day': '1440', 'week': '10080', 'month': '43200', 'year': '525600'}

# safesearch definitions
safesearch_types = {2: 'STRICT', 1: 'DEMOTE', 0: 'OFF'}


# do search-request
def request(query, params):
    offset = ((params['pageno'] - 1) * number_of_results) + 1

    search_path = search_string.format(query=urlencode({'q': query}), count=number_of_results, first=offset)

    language = match_language(params['language'], supported_languages, language_aliases).lower()

    params['cookies']['SRCHHPGUSR'] = 'ADLT=' + safesearch_types.get(params['safesearch'], 'DEMOTE')

    params['cookies']['_EDGE_S'] = 'mkt=' + language + '&ui=' + language + '&F=1'

    params['url'] = base_url + search_path
    if params['time_range'] in time_range_dict:
        params['url'] += time_range_string.format(interval=time_range_dict[params['time_range']])

    return params


# get response from search-request
def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    # parse results
    for result in dom.xpath('//div[@class="imgpt"]'):
        img_format = result.xpath('./div[contains(@class, "img_info")]/span/text()')[0]
        # Microsoft seems to experiment with this code so don't make the path too specific,
        # just catch the text section for the first anchor in img_info assuming this to be
        # the originating site.
        source = result.xpath('./div[contains(@class, "img_info")]//a/text()')[0]

        m = loads(result.xpath('./a/@m')[0])

        # strip 'Unicode private use area' highlighting, they render to Tux
        # the Linux penguin and a standing diamond on my machine...
        title = m.get('t', '').replace('\ue000', '').replace('\ue001', '')
        results.append(
            {
                'template': 'images.html',
                'url': m['purl'],
                'thumbnail_src': m['turl'],
                'img_src': m['murl'],
                'content': '',
                'title': title,
                'source': source,
                'img_format': img_format,
            }
        )

    return results


def fetch_traits(engine_traits: EngineTraits):
    """Fetch languages and regions from Bing-News."""
    # pylint: disable=import-outside-toplevel

    from searx.engines.bing import _fetch_traits

    url = 'https://learn.microsoft.com/en-us/bing/search-apis/bing-news-search/reference/market-codes'

    xpath_market_codes = '//table[1]/tbody/tr/td[3]'

    # xpath_country_codes = '//table[2]/tbody/tr/td[2]'
    xpath_language_codes = '//table[3]/tbody/tr/td[2]'

    _fetch_traits(engine_traits, url, xpath_language_codes, xpath_market_codes)
