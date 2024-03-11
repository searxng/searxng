# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bing-News: description see :py:obj:`searx.engines.bing`.

.. hint::

   Bing News is *different* in some ways!

"""

# pylint: disable=invalid-name

from typing import TYPE_CHECKING
from urllib.parse import urlencode

from lxml import html

from searx.utils import eval_xpath, extract_text, eval_xpath_list, eval_xpath_getindex
from searx.enginelib.traits import EngineTraits
from searx.engines.bing import set_bing_cookies

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
"""If go through the pages and there are actually no new results for another
page, then bing returns the results from the last page again."""

time_range_support = True
time_map = {
    'day': 'interval="4"',
    'week': 'interval="7"',
    'month': 'interval="9"',
}
"""A string '4' means *last hour*.  We use *last hour* for ``day`` here since the
difference of *last day* and *last week* in the result list is just marginally.
Bing does not have news range ``year`` / we use ``month`` instead."""

base_url = 'https://www.bing.com/news/infinitescrollajax'
"""Bing (News) search URL"""


def request(query, params):
    """Assemble a Bing-News request."""

    engine_region = traits.get_region(params['searxng_locale'], traits.all_locale)  # type: ignore
    engine_language = traits.get_language(params['searxng_locale'], 'en')  # type: ignore
    set_bing_cookies(params, engine_language, engine_region)

    # build URL query
    #
    # example: https://www.bing.com/news/infinitescrollajax?q=london&first=1

    page = int(params.get('pageno', 1)) - 1
    query_params = {
        'q': query,
        'InfiniteScroll': 1,
        # to simplify the page count lets use the default of 10 images per page
        'first': page * 10 + 1,
        'SFX': page,
        'form': 'PTFTNR',
        'setlang': engine_region.split('-')[0],
        'cc': engine_region.split('-')[-1],
    }

    if params['time_range']:
        query_params['qft'] = time_map.get(params['time_range'], 'interval="9"')

    params['url'] = base_url + '?' + urlencode(query_params)

    return params


def response(resp):
    """Get response from Bing-Video"""
    results = []

    if not resp.ok or not resp.text:
        return results

    dom = html.fromstring(resp.text)

    for newsitem in eval_xpath_list(dom, '//div[contains(@class, "newsitem")]'):

        link = eval_xpath_getindex(newsitem, './/a[@class="title"]', 0, None)
        if link is None:
            continue
        url = link.attrib.get('href')
        title = extract_text(link)
        content = extract_text(eval_xpath(newsitem, './/div[@class="snippet"]'))

        metadata = []
        source = eval_xpath_getindex(newsitem, './/div[contains(@class, "source")]', 0, None)
        if source is not None:
            for item in (
                eval_xpath_getindex(source, './/span[@aria-label]/@aria-label', 0, None),
                # eval_xpath_getindex(source, './/a', 0, None),
                # eval_xpath_getindex(source, './div/span', 3, None),
                link.attrib.get('data-author'),
            ):
                if item is not None:
                    t = extract_text(item)
                    if t and t.strip():
                        metadata.append(t.strip())
        metadata = ' | '.join(metadata)

        thumbnail = None
        imagelink = eval_xpath_getindex(newsitem, './/a[@class="imagelink"]//img', 0, None)
        if imagelink is not None:
            thumbnail = 'https://www.bing.com/' + imagelink.attrib.get('src')

        results.append(
            {
                'url': url,
                'title': title,
                'content': content,
                'img_src': thumbnail,
                'metadata': metadata,
            }
        )

    return results


def fetch_traits(engine_traits: EngineTraits):
    """Fetch languages and regions from Bing-News."""
    # pylint: disable=import-outside-toplevel

    from searx.engines.bing import fetch_traits as _f

    _f(engine_traits)

    # fix market codes not known by bing news:

    # In bing the market code 'zh-cn' exists, but there is no 'news' category in
    # bing for this market.  Alternatively we use the the market code from Honk
    # Kong.  Even if this is not correct, it is better than having no hits at
    # all, or sending false queries to bing that could raise the suspicion of a
    # bot.

    # HINT: 'en-hk' is the region code it does not indicate the language en!!
    engine_traits.regions['zh-CN'] = 'en-hk'
