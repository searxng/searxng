# SPDX-License-Identifier: AGPL-3.0-or-later
"""Yep (general, images, news)"""

import typing as t

from urllib.parse import urlencode

from searx.result_types import EngineResults
from searx.utils import html_to_text

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    'website': 'https://yep.com/',
    'official_api_documentation': 'https://docs.developer.yelp.com',
    'use_official_api': False,
    'require_api_key': False,
    'results': 'JSON',
}

base_url = "https://api.yep.com"

safesearch = True
safesearch_map = {0: 'off', 1: 'moderate', 2: 'strict'}

enable_http2 = False

results_per_page = 20


def request(query: str, params: 'OnlineParams') -> None:
    args = {'query': query, 'safeSearch': safesearch_map[params['safesearch']], 'limit': results_per_page}
    params['url'] = f"{base_url}/fs/2/search?{urlencode(args)}"
    params['headers']['Referer'] = 'https://yep.com/'
    params['headers']['Origin'] = 'https://yep.com'


def response(resp: 'SXNG_Response') -> EngineResults:
    res = EngineResults()

    for result in resp.json()[1]['results']:
        res.add(
            res.types.MainResult(
                url=result['url'],
                title=result['title'],
                content=html_to_text(result['snippet']),
            )
        )

    return res
