# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deviantart (Images)"""

import typing as t

import urllib.parse
from lxml import html

from searx.result_types import EngineResults
from searx.utils import extract_text, eval_xpath, eval_xpath_list

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

# about
about = {
    "website": 'https://www.deviantart.com/',
    "wikidata_id": 'Q46523',
    "official_api_documentation": 'https://www.deviantart.com/developers/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['images']
paging = True

# search-url
base_url = 'https://www.deviantart.com'

results_xpath = '//div[@data-testid="content_row"]//a[.//*[@data-testid="thumb"]]'
img_src_xpath = './/img/@srcset'
thumbnail_src_xpath = './/img/@src'
author_xpath = './/*[@property="schema:name"]/@content'
cursor_xpath = '//a[contains(@href, "cursor=") and contains(., "Next")]/@href'


def request(query: str, params: "OnlineParams"):
    # https://www.deviantart.com/search?q=foo

    args = {'q': query}
    if params['pageno'] > 1:
        cursor = params['engine_data'].get('cursor')
        if cursor:
            args['cursor'] = cursor

    params['url'] = f"{base_url}/search?{urllib.parse.urlencode(args)}"


def response(resp: "SXNG_Response") -> EngineResults:

    res = EngineResults()
    dom = html.fromstring(resp.text)

    for result in eval_xpath_list(dom, results_xpath):
        thumbnail_src = extract_text(eval_xpath(result, thumbnail_src_xpath))
        img_src = extract_text(eval_xpath(result, img_src_xpath))
        # mature locked thumbs have blur transform (blur_15, blur_30 etc..)
        if ',blur_' in f'{thumbnail_src}{img_src}':
            continue
        if img_src:
            img_src = img_src.split(' ')[0]
            parsed_url = urllib.parse.urlparse(img_src)
            img_src = parsed_url._replace(path=parsed_url.path.split('/v1')[0]).geturl()

        author = extract_text(eval_xpath(result, author_xpath))

        res.add(
            res.types.Image(
                template='images.html',
                url=result.get('href'),
                img_src=img_src or "",
                thumbnail_src=thumbnail_src or "",
                title=result.get('aria-label'),
                author=author or "",
            )
        )

    nextpage_url = extract_text(eval_xpath(dom, cursor_xpath))
    cursor = urllib.parse.parse_qs(urllib.parse.urlparse(nextpage_url or '').query).get('cursor', [None])[0]
    if cursor:
        res.add(
            res.types.LegacyResult(
                engine_data=cursor,
                key='cursor',
            )
        )

    return res
