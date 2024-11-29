# SPDX-License-Identifier: AGPL-3.0-or-later

"""This is the implementation of the Mullvad-Leta meta-search engine.

This engine **REQUIRES** that searxng operate within a Mullvad VPN

If using docker, consider using gluetun for easily connecting to the Mullvad

- https://github.com/qdm12/gluetun

Otherwise, follow instructions provided by Mullvad for enabling the VPN on Linux

- https://mullvad.net/en/help/install-mullvad-app-linux

.. hint::

   The :py:obj:`EngineTraits` is empty by default.  Maintainers have to run
   ``make data.traits`` (in the Mullvad VPN / :py:obj:`fetch_traits`) and rebase
   the modified JSON file ``searx/data/engine_traits.json`` on every single
   update of SearXNG!
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from httpx import Response
from lxml import html
from searx.enginelib.traits import EngineTraits
from searx.locales import region_tag, get_official_locales
from searx.utils import eval_xpath, extract_text, eval_xpath_list
from searx.exceptions import SearxEngineResponseException

if TYPE_CHECKING:
    import logging

    logger = logging.getLogger()

traits: EngineTraits

use_cache: bool = True  # non-cache use only has 100 searches per day!

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
max_page = 50
time_range_support = True
time_range_dict = {
    "day": "d1",
    "week": "w1",
    "month": "m1",
    "year": "y1",
}

available_leta_engines = [
    'google',  # first will be default if provided engine is invalid
    'brave',
]


def is_vpn_connected(dom: html.HtmlElement) -> bool:
    """Returns true if the VPN is connected, False otherwise"""
    connected_text = extract_text(eval_xpath(dom, '//main/div/p[1]'))
    return connected_text != 'You are not connected to Mullvad VPN.'


def assign_headers(headers: dict) -> dict:
    """Assigns the headers to make a request to Mullvad Leta"""
    headers['Accept'] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    headers['Content-Type'] = "application/x-www-form-urlencoded"
    headers['Host'] = "leta.mullvad.net"
    headers['Origin'] = "https://leta.mullvad.net"
    return headers


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

    params['url'] = search_url
    params['method'] = 'POST'
    params['data'] = {
        "q": query,
        "gl": country if country is str else '',
        'engine': result_engine,
    }
    # pylint: disable=undefined-variable
    if use_cache:
        params['data']['oc'] = "on"
    # pylint: enable=undefined-variable

    if params['time_range'] in time_range_dict:
        params['dateRestrict'] = time_range_dict[params['time_range']]
    else:
        params['dateRestrict'] = ''

    if params['pageno'] > 1:
        #  Page 1 is n/a, Page 2 is 11, page 3 is 21, ...
        params['data']['start'] = ''.join([str(params['pageno'] - 1), "1"])

    if params['headers'] is None:
        params['headers'] = {}

    assign_headers(params['headers'])
    return params


def extract_result(dom_result: list[html.HtmlElement]):
    # Infoboxes sometimes appear in the beginning and will have a length of 0
    if len(dom_result) == 3:
        [a_elem, h3_elem, p_elem] = dom_result
    elif len(dom_result) == 4:
        [_, a_elem, h3_elem, p_elem] = dom_result
    else:
        return None

    return {
        'url': extract_text(a_elem.text),
        'title': extract_text(h3_elem),
        'content': extract_text(p_elem),
    }


def extract_results(search_results: html.HtmlElement):
    for search_result in search_results:
        dom_result = eval_xpath_list(search_result, 'div/div/*')
        result = extract_result(dom_result)
        if result is not None:
            yield result


def response(resp: Response):
    """Checks if connected to Mullvad VPN, then extracts the search results from
    the DOM resp: requests response object"""

    dom = html.fromstring(resp.text)
    if not is_vpn_connected(dom):
        raise SearxEngineResponseException('Not connected to Mullvad VPN')
    search_results = eval_xpath(dom.body, '//main/div[2]/div')
    return list(extract_results(search_results))


def fetch_traits(engine_traits: EngineTraits):
    """Fetch languages and regions from Mullvad-Leta

    .. warning::

        Fetching the engine traits also requires a Mullvad VPN connection. If
        not connected, then an error message will print and no traits will be
        updated.
    """
    # pylint: disable=import-outside-toplevel
    # see https://github.com/searxng/searxng/issues/762
    from searx.network import post as http_post

    # pylint: enable=import-outside-toplevel
    resp = http_post(search_url, headers=assign_headers({}))
    if not isinstance(resp, Response):
        print("ERROR: failed to get response from mullvad-leta. Are you connected to the VPN?")
        return
    if not resp.ok:
        print("ERROR: response from mullvad-leta is not OK. Are you connected to the VPN?")
        return
    dom = html.fromstring(resp.text)
    if not is_vpn_connected(dom):
        print('ERROR: Not connected to Mullvad VPN')
        return
    # supported region codes
    options = eval_xpath_list(dom.body, '//main/div/form/div[2]/div/select[1]/option')
    if options is None or len(options) <= 0:
        print('ERROR: could not find any results. Are you connected to the VPN?')
    for x in options:
        eng_country = x.get("value")

        sxng_locales = get_official_locales(eng_country, engine_traits.languages.keys(), regional=True)

        if not sxng_locales:
            print(
                "ERROR: can't map from Mullvad-Leta country %s (%s) to a babel region."
                % (x.get('data-name'), eng_country)
            )
            continue

        for sxng_locale in sxng_locales:
            engine_traits.regions[region_tag(sxng_locale)] = eng_country
