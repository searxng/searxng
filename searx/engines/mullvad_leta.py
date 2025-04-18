# SPDX-License-Identifier: AGPL-3.0-or-later

"""This is the implementation of the Mullvad-Leta meta-search engine.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict
from urllib.parse import urlencode
import babel
from httpx import Response
from lxml import html
from searx.enginelib.traits import EngineTraits
from searx.locales import get_official_locales, language_tag, region_tag
from searx.utils import eval_xpath_list
from searx.result_types import EngineResults, MainResult

if TYPE_CHECKING:
    import logging

    logger = logging.getLogger()

traits: EngineTraits

leta_engine: str = 'google'

search_url = "https://leta.mullvad.net"

# about
about = {
    "website": search_url,
    "wikidata_id": 'Q47008412',  # the Mullvad id - not leta, but related
    "official_api_documentation": 'https://leta.mullvad.net/faq',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['general', 'web']
paging = True
max_page = 10
time_range_support = True
time_range_dict = {
    "day": "d",
    "week": "w",
    "month": "m",
    "year": "y",
}

available_leta_engines = [
    'google',  # first will be default if provided engine is invalid
    'brave',
]


class DataNodeQueryMetaDataIndices(TypedDict):
    """Indices into query metadata"""

    success: int
    q: int  # pylint: disable=invalid-name
    country: int
    language: int
    lastUpdated: int
    engine: int
    items: int
    infobox: int
    news: int
    timestamp: int
    altered: int
    page: int
    next: int  # if -1, there no more results are available
    previous: int


class DataNodeResultIndices(TypedDict):
    """Indices into query resultsdata"""

    link: int
    snippet: int
    title: int
    favicon: int


def request(query: str, params: dict):
    country = traits.get_region(params.get('searxng_locale', 'all'), traits.all_locale)  # type: ignore

    result_engine = leta_engine
    if leta_engine not in available_leta_engines:
        result_engine = available_leta_engines[0]
        logger.warning(
            'Configured engine "%s" not one of the available engines %s, defaulting to "%s"',
            leta_engine,
            available_leta_engines,
            result_engine,
        )

    params['method'] = 'GET'

    args = {
        'q': query,
        'engine': result_engine,
        'x-sveltekit-invalidated': "001",  # hardcoded from all requests seen
    }
    if isinstance(country, str):
        args['country'] = country
    if params['time_range'] in time_range_dict:
        args['lastUpdated'] = time_range_dict[params['time_range']]
    if params['pageno'] > 1:
        args['page'] = params['pageno']

    params['url'] = f"{search_url}/search/__data.json?{urlencode(args)}"

    return params


def response(resp: Response) -> EngineResults:
    json_response = resp.json()

    nodes = json_response["nodes"]
    # 0: is None
    # 1: has "connected=True", not useful
    # 2: query results within "data"

    data_nodes = nodes[2]["data"]
    # Instead of nested object structure, all objects are flattened into a
    # list. Rather, the first object in data_node provides indices into the
    # "data_nodes" to access each searchresult (which is an object of more
    # indices)
    #
    # Read the relative TypedDict definitions for details

    query_meta_data: DataNodeQueryMetaDataIndices = data_nodes[0]

    query_items_indices = query_meta_data['items']

    results = EngineResults()
    for idx in data_nodes[query_items_indices]:
        query_item_indices: DataNodeResultIndices = data_nodes[idx]
        results.add(
            MainResult(
                url=data_nodes[query_item_indices['link']],
                title=data_nodes[query_item_indices['title']],
                content=data_nodes[query_item_indices['snippet']],
            )
        )

    return results


def fetch_traits(engine_traits: EngineTraits) -> None:
    """Fetch languages and regions from Mullvad-Leta"""

    def extract_table_data(table):
        for row in table.xpath('.//tr')[2:]:
            cells = row.xpath('.//td | .//th')  # includes headers and data
            if len(cells) > 1:  # ensure the column exists
                cell0 = cells[0].text_content().strip()
                cell1 = cells[1].text_content().strip()
                yield [cell0, cell1]

    # pylint: disable=import-outside-toplevel
    # see https://github.com/searxng/searxng/issues/762
    from searx.network import get as http_get

    # pylint: enable=import-outside-toplevel
    resp = http_get(f'{search_url}/documentation')
    if not isinstance(resp, Response):
        print("ERROR: failed to get response from mullvad-leta. Are you connected to the VPN?")
        return
    if not resp.ok:
        print("ERROR: response from mullvad-leta is not OK. Are you connected to the VPN?")
        return

    dom = html.fromstring(resp.text)

    # There are 4 HTML tables on the documentation page for extracting information:
    # 0. Keyboard Shortcuts
    # 1. Query Parameters (shoutout to Mullvad for accessible docs for integration)
    # 2. Country Codes [Country, Code]
    # 3. Language Codes [Language, Code]
    tables = eval_xpath_list(dom.body, '//table')
    if tables is None or len(tables) <= 0:
        print('ERROR: could not find any tables. Was the page updated?')

    country_table = tables[2]
    language_table = tables[3]

    language_fixes = {
        'jp': 'ja_JP',
    }

    for language, code in extract_table_data(language_table):
        try:
            sxng_tag = language_tag(babel.Locale.parse(language_fixes.get(code, code).replace("-", "_")))
            engine_traits.languages[sxng_tag] = code
        except babel.UnknownLocaleError:
            print("ERROR: Mullvad-Leta language (%s) (%s) is unknown by babel" % (language, code))
            continue

    country_to_lang_fixes = {
        'id': 'id',
        'jp': 'ja',
        'my': 'ms',
        'tw': 'zh_Hant',
        'uk': 'en',
    }
    for country, code in extract_table_data(country_table):
        try:
            if code in country_to_lang_fixes:
                lang_to_region = country_to_lang_fixes[code] + "_" + code
                sxng_tag = language_tag(babel.Locale.parse(lang_to_region))
                engine_traits.languages[sxng_tag] = code
            else:
                sxng_locales = get_official_locales(code, engine_traits.languages.keys(), regional=True)
                if not sxng_locales:
                    print("ERROR: Mullvad-Leta country (%s) (%s) could not be mapped as expected." % (code, country))
                    continue
                for sxng_locale in sxng_locales:
                    engine_traits.regions[region_tag(sxng_locale)] = code
        except babel.UnknownLocaleError:
            print("ERROR: Mullvad-Leta country (%s) (%s) is unknown by babel" % (code, country))
            continue
