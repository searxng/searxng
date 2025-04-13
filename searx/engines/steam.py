# SPDX-License-Identifier: AGPL-3.0-or-later
"""Steam (store) for SearXNG."""

from urllib.parse import urlencode

from searx.utils import html_to_text
from searx.result_types import EngineResults, MainResult

about = {
    "website": 'https://store.steampowered.com/',
    "wikidata_id": 'Q337535',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

categories = []

base_url = "https://store.steampowered.com"


def request(query, params):
    query_params = {"term": query, "cc": "us", "l": "en"}
    params['url'] = f'{base_url}/api/storesearch/?{urlencode(query_params)}'
    return params


def response(resp) -> EngineResults:
    results = EngineResults()
    search_results = resp.json()

    for item in search_results.get('items', []):
        app_id = item.get('id')

        currency = item.get('price', {}).get('currency', 'USD')
        price = item.get('price', {}).get('final', 0) / 100

        platforms = ', '.join([platform for platform, supported in item.get('platforms', {}).items() if supported])

        content = [f'Price: {price:.2f} {currency}', f'Platforms: {platforms}']

        results.add(
            MainResult(
                title=item.get('name'),
                content=html_to_text(' | '.join(content)),
                url=f'{base_url}/app/{app_id}',
                thumbnail=item.get('tiny_image', ''),
            )
        )

    return results
