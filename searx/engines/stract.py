# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stract is an independent open source search engine.  At this state, it's
still in beta and hence this implementation will need to be updated once beta
ends.

"""

from json import dumps
from searx.utils import searxng_useragent
from searx.enginelib.traits import EngineTraits

about = {
    "website": "https://stract.com/",
    "use_official_api": True,
    "official_api_documentation": "https://stract.com/beta/api/docs/#/search/api",
    "require_api_key": False,
    "results": "JSON",
}
categories = ['general']
paging = True

base_url = "https://stract.com/beta/api"
search_url = base_url + "/search"

traits: EngineTraits


def request(query, params):
    params['url'] = search_url
    params['method'] = "POST"
    params['headers'] = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': searxng_useragent(),
    }
    region = traits.get_region(params["searxng_locale"], default=traits.all_locale)
    params['data'] = dumps(
        {
            'query': query,
            'page': params['pageno'] - 1,
            'selectedRegion': region,
        }
    )

    return params


def response(resp):
    results = []

    for result in resp.json()["webpages"]:
        results.append(
            {
                'url': result['url'],
                'title': result['title'],
                'content': ''.join(fragment['text'] for fragment in result['snippet']['text']['fragments']),
            }
        )

    return results


def fetch_traits(engine_traits: EngineTraits):
    # pylint: disable=import-outside-toplevel
    from searx import network
    from babel import Locale, languages
    from searx.locales import region_tag

    territories = Locale("en").territories

    json = network.get(base_url + "/docs/openapi.json").json()
    regions = json['components']['schemas']['Region']['enum']

    engine_traits.all_locale = regions[0]

    for region in regions[1:]:
        for code, name in territories.items():
            if region not in (code, name):
                continue
            for lang in languages.get_official_languages(code, de_facto=True):
                engine_traits.regions[region_tag(Locale(lang, code))] = region
