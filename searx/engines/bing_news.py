# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Bing-News: description see :py:obj:`searx.engines.bing`.
"""

# pylint: disable=invalid-name

from typing import TYPE_CHECKING
import uuid
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
    "website": 'https://www.bing.com/news',
    "wikidata_id": 'Q2878637',
    "official_api_documentation": 'https://www.microsoft.com/en-us/bing/apis/bing-news-search-api',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'RSS',
}

# engine dependent config
categories = ['news']
paging = True
time_range_support = True
time_map = {
    'day': '4',
    'week': '8',
    'month': '9',
}
"""A string '4' means *last hour*. We use *last hour* for ``day`` here since the
difference of *last day* and *last week* in the result list is just marginally.
"""

base_url = 'https://www.bing.com/news/infinitescrollajax'
"""Bing (News) search URL"""

bing_traits_url = 'https://learn.microsoft.com/en-us/bing/search-apis/bing-news-search/reference/market-codes'
"""Bing (News) search API description"""

mkt_alias = {
    'zh': 'en-WW',
    'zh-CN': 'en-WW',
}
"""Bing News has an official market code 'zh-CN' but we won't get a result with
this market code.  For 'zh' and 'zh-CN' we better use the *Worldwide aggregate*
market code (en-WW).
"""


def request(query, params):
    """Assemble a Bing-News request."""

    sxng_locale = params['searxng_locale']
    engine_region = traits.get_region(mkt_alias.get(sxng_locale, sxng_locale), traits.all_locale)
    engine_language = traits.get_language(sxng_locale, 'en')

    SID = uuid.uuid1().hex.upper()
    set_bing_cookies(params, engine_language, engine_region, SID)

    # build URL query
    #
    # example: https://www.bing.com/news/infinitescrollajax?q=london&first=1

    query_params = {
        # fmt: off
        'q': query,
        'InfiniteScroll': 1,
        # to simplify the page count lets use the default of 10 images per page
        'first' : (int(params.get('pageno', 1)) - 1) * 10 + 1,
        # fmt: on
    }

    if params['time_range']:
        # qft=interval:"7"
        query_params['qft'] = 'qft=interval="%s"' % time_map.get(params['time_range'], '9')

    params['url'] = base_url + '?' + urlencode(query_params)

    return params


def response(resp):
    """Get response from Bing-Video"""
    results = []

    if not resp.ok or not resp.text:
        return results

    dom = html.fromstring(resp.text)

    for newsitem in dom.xpath('//div[contains(@class, "newsitem")]'):

        url = newsitem.xpath('./@url')[0]
        title = ' '.join(newsitem.xpath('.//div[@class="caption"]//a[@class="title"]/text()')).strip()
        content = ' '.join(newsitem.xpath('.//div[@class="snippet"]/text()')).strip()
        thumbnail = None
        author = newsitem.xpath('./@data-author')[0]
        metadata = ' '.join(newsitem.xpath('.//div[@class="source"]/span/text()')).strip()

        img_src = newsitem.xpath('.//a[@class="imagelink"]//img/@src')
        if img_src:
            thumbnail = 'https://www.bing.com/' + img_src[0]

        results.append(
            {
                'url': url,
                'title': title,
                'content': content,
                'img_src': thumbnail,
                'author': author,
                'metadata': metadata,
            }
        )

    return results


def fetch_traits(engine_traits: EngineTraits):
    """Fetch languages and regions from Bing-News.

    The :py:obj:`description <searx.engines.bing_news.bing_traits_url>` of the
    first table says *"query parameter when calling the Video Search API."*
    .. thats why I use the 4. table "News Category API markets" for the
    ``xpath_market_codes``.

    """

    xpath_market_codes = '//table[4]/tbody/tr/td[3]'
    # xpath_country_codes = '//table[2]/tbody/tr/td[2]'
    xpath_language_codes = '//table[3]/tbody/tr/td[2]'

    _fetch_traits(engine_traits, bing_traits_url, xpath_language_codes, xpath_market_codes)
