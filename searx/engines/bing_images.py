# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Bing-Images: description see :py:obj:`searx.engines.bing`.
"""
# pylint: disable=invalid-name


from typing import TYPE_CHECKING
import uuid
import json
from urllib.parse import urlencode

from lxml import html

from searx.enginelib.traits import EngineTraits
from searx.engines.bing import (
    set_bing_cookies,
    _fetch_traits,
)
from searx.engines.bing import send_accept_language_header  # pylint: disable=unused-import

if TYPE_CHECKING:
    import logging

    logger: logging.Logger

traits: EngineTraits

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

base_url = 'https://www.bing.com/images/async'
"""Bing (Images) search URL"""

bing_traits_url = 'https://learn.microsoft.com/en-us/bing/search-apis/bing-image-search/reference/market-codes'
"""Bing (Images) search API description"""

time_map = {
    # fmt: off
    'day': 60 * 24,
    'week': 60 * 24 * 7,
    'month': 60 * 24 * 31,
    'year': 60 * 24 * 365,
    # fmt: on
}


def request(query, params):
    """Assemble a Bing-Image request."""

    engine_region = traits.get_region(params['searxng_locale'], 'en-US')
    engine_language = traits.get_language(params['searxng_locale'], 'en')

    SID = uuid.uuid1().hex.upper()
    set_bing_cookies(params, engine_language, engine_region, SID)

    # build URL query
    # - example: https://www.bing.com/images/async?q=foo&first=155&count=35

    query_params = {
        # fmt: off
        'q': query,
        'async' : 'content',
        # to simplify the page count lets use the default of 35 images per page
        'first' : (int(params.get('pageno', 1)) - 1) * 35 + 1,
        'count' : 35,
        # fmt: on
    }

    # time range
    # - example: one year (525600 minutes) 'qft=+filterui:age-lt525600'

    if params['time_range']:
        query_params['qft'] = 'filterui:age-lt%s' % time_map[params['time_range']]

    params['url'] = base_url + '?' + urlencode(query_params)

    return params


def response(resp):
    """Get response from Bing-Images"""

    results = []
    dom = html.fromstring(resp.text)

    for result in dom.xpath('//ul[contains(@class, "dgControl_list")]/li'):

        metadata = result.xpath('.//a[@class="iusc"]/@m')
        if not metadata:
            continue

        metadata = json.loads(result.xpath('.//a[@class="iusc"]/@m')[0])
        title = ' '.join(result.xpath('.//div[@class="infnmpt"]//a/text()')).strip()
        img_format = ' '.join(result.xpath('.//div[@class="imgpt"]/div/span/text()')).strip()
        source = ' '.join(result.xpath('.//div[@class="imgpt"]//div[@class="lnkw"]//a/text()')).strip()
        results.append(
            {
                'template': 'images.html',
                'url': metadata['purl'],
                'thumbnail_src': metadata['turl'],
                'img_src': metadata['murl'],
                'content': metadata['desc'],
                'title': title,
                'source': source,
                'img_format': img_format,
            }
        )
    return results


def fetch_traits(engine_traits: EngineTraits):
    """Fetch languages and regions from Bing-News."""

    xpath_market_codes = '//table[1]/tbody/tr/td[3]'
    # xpath_country_codes = '//table[2]/tbody/tr/td[2]'
    xpath_language_codes = '//table[3]/tbody/tr/td[2]'

    _fetch_traits(engine_traits, bing_traits_url, xpath_language_codes, xpath_market_codes)
