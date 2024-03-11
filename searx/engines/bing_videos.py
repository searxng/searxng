# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=invalid-name
"""Bing-Videos: description see :py:obj:`searx.engines.bing`.
"""

from typing import TYPE_CHECKING
import json
from urllib.parse import urlencode

from lxml import html

from searx.enginelib.traits import EngineTraits
from searx.engines.bing import set_bing_cookies
from searx.engines.bing import fetch_traits  # pylint: disable=unused-import
from searx.engines.bing_images import time_map

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


def request(query, params):
    """Assemble a Bing-Video request."""

    engine_region = traits.get_region(params['searxng_locale'], traits.all_locale)  # type: ignore
    engine_language = traits.get_language(params['searxng_locale'], 'en')  # type: ignore
    set_bing_cookies(params, engine_language, engine_region)

    # build URL query
    #
    # example: https://www.bing.com/videos/asyncv2?q=foo&async=content&first=1&count=35

    query_params = {
        'q': query,
        'async': 'content',
        # to simplify the page count lets use the default of 35 images per page
        'first': (int(params.get('pageno', 1)) - 1) * 35 + 1,
        'count': 35,
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
