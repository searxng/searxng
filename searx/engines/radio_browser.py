# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Radio browser (music)
"""

from urllib.parse import urlencode
import babel

from searx.network import get
from searx.enginelib.traits import EngineTraits
from searx.locales import language_tag, region_tag

traits: EngineTraits

about = {
    "website": 'https://www.radio-browser.info/',
    "official_api_documentation": 'https://de1.api.radio-browser.info/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}
paging = True
categories = ['music']

base_url = "https://de1.api.radio-browser.info"  # see https://api.radio-browser.info/ for all nodes
number_of_results = 10


def request(query, params):
    args = {
        'name': query,
        'order': 'votes',
        'offset': (params['pageno'] - 1) * number_of_results,
        'limit': number_of_results,
        'hidebroken': 'true',
        'reverse': 'true',
    }
    lang = traits.get_language(params['searxng_locale'], None)
    if lang is not None:
        args['language'] = lang

    region = traits.get_region(params['searxng_locale'], None)
    if region is not None:
        args['countrycode'] = region.split('-')[1]

    params['url'] = f"{base_url}/json/stations/search?{urlencode(args)}"
    return params


def response(resp):
    results = []

    for result in resp.json():
        url = result['homepage']
        if not url:
            url = result['url_resolved']

        results.append(
            {
                'template': 'videos.html',
                'url': url,
                'title': result['name'],
                'thumbnail': result.get('favicon', '').replace("http://", "https://"),
                'content': result['country']
                + " / "
                + result["tags"]
                + f" / {result['votes']} votes"
                + f" / {result['clickcount']} clicks",
                'iframe_src': result['url_resolved'].replace("http://", "https://"),
            }
        )

    return results


def fetch_traits(engine_traits: EngineTraits):
    language_list = get(f'{base_url}/json/languages').json()

    country_list = get(f'{base_url}/json/countrycodes').json()

    for lang in language_list:

        # the language doesn't have any iso code, and hence can't be parsed
        if not lang['iso_639']:
            continue

        try:
            lang_tag = lang['iso_639']
            sxng_tag = language_tag(babel.Locale.parse(lang_tag, sep="-"))
        except babel.UnknownLocaleError:
            print("ERROR: %s is unknown by babel" % lang_tag)
            continue

        conflict = engine_traits.languages.get(sxng_tag)
        if conflict:
            continue

        engine_traits.languages[sxng_tag] = lang['name']

        for region in country_list:
            try:
                reg_tag = f"{lang['iso_639']}-{region['name']}"
                sxng_tag = region_tag(babel.Locale.parse(reg_tag, sep="-"))
            except babel.UnknownLocaleError:
                continue

            conflict = engine_traits.regions.get(sxng_tag)
            if conflict:
                continue

            engine_traits.regions[sxng_tag] = reg_tag
