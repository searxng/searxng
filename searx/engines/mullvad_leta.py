# SPDX-License-Identifier: AGPL-3.0-or-later
"""Mullvad Leta is a search engine proxy. Currently Leta only offers text
search results not image, news or any other types of search result.  Leta acts
as a proxy to Google and Brave search results. You can select which backend
search engine you wish to use, see  (:py:obj:`leta_engine`).

.. hint::

   Leta caches each search for up to 30 days.  For example, if you use search
   terms like ``news``, contrary to your intention you'll get very old results!


Configuration
=============

The engine has the following additional settings:

- :py:obj:`leta_engine` (:py:obj:`LetaEnginesType`)

You can configure one Leta engine for Google and one for Brave:

.. code:: yaml

  - name: mullvadleta
    engine: mullvad_leta
    leta_engine: google
    shortcut: ml

  - name: mullvadleta brave
    engine: mullvad_leta
    network: mullvadleta  # use network from engine "mullvadleta" configured above
    leta_engine: brave
    shortcut: mlb

Implementations
===============

"""

from __future__ import annotations

import typing
from urllib.parse import urlencode
import babel
from httpx import Response
from lxml import html
from searx.enginelib.traits import EngineTraits
from searx.locales import get_official_locales, language_tag, region_tag
from searx.utils import eval_xpath_list
from searx.result_types import EngineResults, MainResult

if typing.TYPE_CHECKING:
    import logging

    logger = logging.getLogger()

traits: EngineTraits

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
categories = ["general", "web"]
paging = True
max_page = 10
time_range_support = True
time_range_dict = {
    "day": "d",
    "week": "w",
    "month": "m",
    "year": "y",
}

LetaEnginesType = typing.Literal["google", "brave"]
"""Engine types supported by mullvadleta."""

leta_engine: LetaEnginesType = "google"
"""Select Leta's engine type from :py:obj:`LetaEnginesType`."""


def init(_):
    l = typing.get_args(LetaEnginesType)
    if leta_engine not in l:
        raise ValueError(f"leta_engine '{leta_engine}' is invalid, use one of {', '.join(l)}")


class DataNodeQueryMetaDataIndices(typing.TypedDict):
    """Indices into query metadata."""

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


class DataNodeResultIndices(typing.TypedDict):
    """Indices into query resultsdata."""

    link: int
    snippet: int
    title: int
    favicon: int


def request(query: str, params: dict):
    params["method"] = "GET"
    args = {
        "q": query,
        "engine": leta_engine,
        "x-sveltekit-invalidated": "001",  # hardcoded from all requests seen
    }

    country = traits.get_region(params.get("searxng_locale"), traits.all_locale)  # type: ignore
    if country:
        args["country"] = country

    language = traits.get_language(params.get("searxng_locale"), traits.all_locale)  # type: ignore
    if language:
        args["language"] = language

    if params["time_range"] in time_range_dict:
        args["lastUpdated"] = time_range_dict[params["time_range"]]

    if params["pageno"] > 1:
        args["page"] = params["pageno"]

    params["url"] = f"{search_url}/search/__data.json?{urlencode(args)}"

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

    query_items_indices = query_meta_data["items"]

    results = EngineResults()
    for idx in data_nodes[query_items_indices]:
        query_item_indices: DataNodeResultIndices = data_nodes[idx]
        results.add(
            MainResult(
                url=data_nodes[query_item_indices["link"]],
                title=data_nodes[query_item_indices["title"]],
                content=data_nodes[query_item_indices["snippet"]],
            )
        )

    return results


def fetch_traits(engine_traits: EngineTraits) -> None:
    """Fetch languages and regions from Mullvad-Leta"""

    def extract_table_data(table):
        for row in table.xpath(".//tr")[2:]:
            cells = row.xpath(".//td | .//th")  # includes headers and data
            if len(cells) > 1:  # ensure the column exists
                cell0 = cells[0].text_content().strip()
                cell1 = cells[1].text_content().strip()
                yield [cell0, cell1]

    # pylint: disable=import-outside-toplevel
    # see https://github.com/searxng/searxng/issues/762
    from searx.network import get as http_get

    # pylint: enable=import-outside-toplevel

    resp = http_get(f"{search_url}/documentation")
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
    tables = eval_xpath_list(dom.body, "//table")
    if tables is None or len(tables) <= 0:
        print("ERROR: could not find any tables. Was the page updated?")

    language_table = tables[3]
    lang_map = {
        "zh-hant": "zh_Hans",
        "zh-hans": "zh_Hant",
        "jp": "ja",
    }

    for language, code in extract_table_data(language_table):

        locale_tag = lang_map.get(code, code).replace("-", "_")  # type: ignore
        try:
            locale = babel.Locale.parse(locale_tag)
        except babel.UnknownLocaleError:
            print(f"ERROR: Mullvad-Leta language {language} ({code}) is unknown by babel")
            continue

        sxng_tag = language_tag(locale)
        engine_traits.languages[sxng_tag] = code

    country_table = tables[2]
    country_map = {
        "cn": "zh-CN",
        "hk": "zh-HK",
        "jp": "ja-JP",
        "my": "ms-MY",
        "tw": "zh-TW",
        "uk": "en-GB",
        "us": "en-US",
    }

    for country, code in extract_table_data(country_table):

        sxng_tag = country_map.get(code)
        if sxng_tag:
            engine_traits.regions[sxng_tag] = code
            continue

        try:
            locale = babel.Locale.parse(f"{code.lower()}_{code.upper()}")
        except babel.UnknownLocaleError:
            locale = None

        if locale:
            engine_traits.regions[region_tag(locale)] = code
            continue

        official_locales = get_official_locales(code, engine_traits.languages.keys(), regional=True)
        if not official_locales:
            print(f"ERROR: Mullvad-Leta country '{code}' ({country}) could not be mapped as expected.")
            continue

        for locale in official_locales:
            engine_traits.regions[region_tag(locale)] = code
