# SPDX-License-Identifier: AGPL-3.0-or-later
"""
DuckDuckGo Extra (images, videos, news)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

from datetime import datetime
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
ddg_category = 'images'
"""The category must be any of ``images``, ``videos`` and ``news``
"""
paging = True
safesearch = True
send_accept_language_header = True

safesearch_cookies = {0: '-2', 1: None, 2: '1'}
safesearch_args = {0: '1', 1: None, 2: '1'}

search_path_map = {'images': 'i', 'videos': 'v', 'news': 'news'}


def request(query, params):

    # request needs a vqd argument
    vqd = get_vqd(query)
    if not vqd:
        # some search terms do not have results and therefore no vqd value
        params['url'] = None
        return params

    eng_region = traits.get_region(params['searxng_locale'], traits.all_locale)
    eng_lang = get_ddg_lang(traits, params['searxng_locale'])

    args = {
        'q': query,
        'o': 'json',
        # 'u': 'bing',
        'l': eng_region,
        'f': ',,,,,',
        'vqd': vqd,
    }

    if params['pageno'] > 1:
        args['s'] = (params['pageno'] - 1) * 100

    params['cookies']['ad'] = eng_lang  # zh_CN
    params['cookies']['ah'] = eng_region  # "us-en,de-de"
    params['cookies']['l'] = eng_region  # "hk-tzh"

    safe_search = safesearch_cookies.get(params['safesearch'])
    if safe_search is not None:
        params['cookies']['p'] = safe_search  # "-2", "1"
    safe_search = safesearch_args.get(params['safesearch'])
    if safe_search is not None:
        args['p'] = safe_search  # "-1", "1"

    logger.debug("cookies: %s", params['cookies'])

    params['url'] = f'https://duckduckgo.com/{search_path_map[ddg_category]}.js?{urlencode(args)}'

    return params


def _image_result(result):
    return {
        'template': 'images.html',
        'url': result['url'],
        'title': result['title'],
        'content': '',
        'thumbnail_src': result['thumbnail'],
        'img_src': result['image'],
        'resolution': '%s x %s' % (result['width'], result['height']),
        'source': result['source'],
    }


def _video_result(result):
    return {
        'template': 'videos.html',
        'url': result['content'],
        'title': result['title'],
        'content': result['description'],
        'thumbnail': result['images'].get('small') or result['images'].get('medium'),
        'iframe_src': result['embed_url'],
        'source': result['provider'],
        'length': result['duration'],
        'metadata': result.get('uploader'),
    }


def _news_result(result):
    return {
        'url': result['url'],
        'title': result['title'],
        'content': result['excerpt'],
        'source': result['source'],
        'publishedDate': datetime.utcfromtimestamp(result['date']),
    }


def response(resp):
    results = []
    res_json = resp.json()

    for result in res_json['results']:
        if ddg_category == 'images':
            results.append(_image_result(result))
        elif ddg_category == 'videos':
            results.append(_video_result(result))
        elif ddg_category == 'news':
            results.append(_news_result(result))
        else:
            raise ValueError(f"Invalid duckduckgo category: {ddg_category}")

    return results
