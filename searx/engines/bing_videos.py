# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Bing-Videos: description see :py:obj:`searx.engines.bing`.
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


about = {
    "website": 'https://www.bing.com/videos',
    "wikidata_id": 'Q4914152',
    "official_api_documentation": 'https://www.microsoft.com/en-us/bing/apis/bing-video-search-api',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['videos', 'web']
paging = True
safesearch = True
time_range_support = True

base_url = 'https://www.bing.com/videos/asyncv2'
"""Bing (Videos) async search URL."""

bing_traits_url = 'https://learn.microsoft.com/en-us/bing/search-apis/bing-video-search/reference/market-codes'
"""Bing (Video) search API description"""

time_map = {
    # fmt: off
    'day': 60 * 24,
    'week': 60 * 24 * 7,
    'month': 60 * 24 * 31,
    'year': 60 * 24 * 365,
    # fmt: on
}


def request(query, params):
    """Assemble a Bing-Video request."""

    engine_region = traits.get_region(params['searxng_locale'], 'en-US')
    engine_language = traits.get_language(params['searxng_locale'], 'en')

    SID = uuid.uuid1().hex.upper()
    set_bing_cookies(params, engine_language, engine_region, SID)

    # build URL query
    #
    # example: https://www.bing.com/videos/asyncv2?q=foo&async=content&first=1&count=35

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
    #
    # example: one week (10080 minutes) '&qft= filterui:videoage-lt10080'  '&form=VRFLTR'

    if params['time_range']:
        query_params['form'] = 'VRFLTR'
        query_params['qft'] = ' filterui:videoage-lt%s' % time_map[params['time_range']]

    params['url'] = base_url + '?' + urlencode(query_params)

    return params


def response(resp):
    """Get response from Bing-Video"""
    results = []

    dom = html.fromstring(resp.text)

    for result in dom.xpath('//div[@class="dg_u"]//div[contains(@id, "mc_vtvc_video")]'):
        metadata = json.loads(result.xpath('.//div[@class="vrhdata"]/@vrhm')[0])
        info = ' - '.join(result.xpath('.//div[@class="mc_vtvc_meta_block"]//span/text()')).strip()
        content = '{0} - {1}'.format(metadata['du'], info)
        thumbnail = result.xpath('.//div[contains(@class, "mc_vtvc_th")]//img/@src')[0]

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


def fetch_traits(engine_traits: EngineTraits):
    """Fetch languages and regions from Bing-Videos."""

    xpath_market_codes = '//table[1]/tbody/tr/td[3]'
    # xpath_country_codes = '//table[2]/tbody/tr/td[2]'
    xpath_language_codes = '//table[3]/tbody/tr/td[2]'

    _fetch_traits(engine_traits, bing_traits_url, xpath_language_codes, xpath_market_codes)
