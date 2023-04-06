# SPDX-License-Identifier: AGPL-3.0-or-later
"""
DuckDuckGo Images
~~~~~~~~~~~~~~~~~
"""

from typing import TYPE_CHECKING
from urllib.parse import urlencode

from searx.engines.duckduckgo import fetch_traits  # pylint: disable=unused-import
from searx.engines.duckduckgo import (
    get_ddg_lang,
    get_vqd,
)
from searx.enginelib.traits import EngineTraits

if TYPE_CHECKING:
    import logging

    logger: logging.Logger

traits: EngineTraits

# about
about = {
    "website": 'https://duckduckgo.com/',
    "wikidata_id": 'Q12805',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON (site requires js to get images)',
}

# engine dependent config
categories = ['images', 'web']
paging = True
safesearch = True
send_accept_language_header = True

safesearch_cookies = {0: '-2', 1: None, 2: '1'}
safesearch_args = {0: '1', 1: None, 2: '1'}


def request(query, params):

    eng_region = traits.get_region(params['searxng_locale'], traits.all_locale)
    eng_lang = get_ddg_lang(traits, params['searxng_locale'])

    args = {
        'q': query,
        'o': 'json',
        # 'u': 'bing',
        'l': eng_region,
        'vqd': get_vqd(query, params["headers"]),
    }

    if params['pageno'] > 1:
        args['s'] = (params['pageno'] - 1) * 100

    params['cookies']['ad'] = eng_lang  # zh_CN
    params['cookies']['ah'] = eng_region  # "us-en,de-de"
    params['cookies']['l'] = eng_region  # "hk-tzh"
    logger.debug("cookies: %s", params['cookies'])

    safe_search = safesearch_cookies.get(params['safesearch'])
    if safe_search is not None:
        params['cookies']['p'] = safe_search  # "-2", "1"
    safe_search = safesearch_args.get(params['safesearch'])
    if safe_search is not None:
        args['p'] = safe_search  # "-1", "1"

    args = urlencode(args)
    params['url'] = 'https://duckduckgo.com/i.js?{args}&f={f}'.format(args=args, f=',,,,,')

    params['headers']['Accept'] = 'application/json, text/javascript, */*; q=0.01'
    params['headers']['Referer'] = 'https://duckduckgo.com/'
    params['headers']['X-Requested-With'] = 'XMLHttpRequest'
    logger.debug("headers: %s", params['headers'])

    return params


def response(resp):
    results = []
    res_json = resp.json()

    for result in res_json['results']:
        results.append(
            {
                'template': 'images.html',
                'title': result['title'],
                'content': '',
                'thumbnail_src': result['thumbnail'],
                'img_src': result['image'],
                'url': result['url'],
                'img_format': '%s x %s' % (result['width'], result['height']),
                'source': result['source'],
            }
        )

    return results
