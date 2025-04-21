# SPDX-License-Identifier: AGPL-3.0-or-later
"""Search radio stations from RadioBrowser by `Advanced station search API`_.

.. _Advanced station search API:
   https://de1.api.radio-browser.info/#Advanced_station_search

"""
from __future__ import annotations

import typing
import random
import socket
from urllib.parse import urlencode
import babel
from flask_babel import gettext

from searx.network import get
from searx.enginelib import EngineCache
from searx.enginelib.traits import EngineTraits
from searx.locales import language_tag

if typing.TYPE_CHECKING:
    import logging

    logger = logging.getLogger()

traits: EngineTraits

about = {
    "website": 'https://www.radio-browser.info/',
    "wikidata_id": 'Q111664849',
    "official_api_documentation": 'https://de1.api.radio-browser.info/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}
paging = True
categories = ['music', 'radio']

number_of_results = 10

station_filters = []  # ['countrycode', 'language']
"""A list of filters to be applied to the search of radio stations.  By default
none filters are applied. Valid filters are:

``language``
  Filter stations by selected language.  For instance the ``de`` from ``:de-AU``
  will be translated to `german` and used in the argument ``language=``.

``countrycode``
  Filter stations by selected country.  The 2-digit countrycode of the station
  comes from the region the user selected.  For instance ``:de-AU`` will filter
  out all stations not in ``AU``.

.. note::

   RadioBrowser has registered a lot of languages and countrycodes unknown to
   :py:obj:`babel` and note that when searching for radio stations, users are
   more likely to search by name than by region or language.

"""

CACHE: EngineCache
"""Persistent (SQLite) key/value cache that deletes its values after ``expire``
seconds."""


def init(_):
    global CACHE  # pylint: disable=global-statement
    CACHE = EngineCache("radio_browser")
    server_list()


def server_list() -> list[str]:

    servers = CACHE.get("servers", [])
    if servers:
        return servers

    # hint: can take up to 40sec!
    ips = socket.getaddrinfo("all.api.radio-browser.info", 80, 0, 0, socket.IPPROTO_TCP)
    for ip_tuple in ips:
        _ip: str = ip_tuple[4][0]  # type: ignore
        url = socket.gethostbyaddr(_ip)[0]
        srv = "https://" + url
        if srv not in servers:
            servers.append(srv)

    # update server list once in 24h
    CACHE.set(key="servers", value=servers, expire=60 * 60 * 24)

    return servers


def request(query, params):

    servers = server_list()
    if not servers:
        logger.error("Fetched server list is empty!")
        params["url"] = None
        return

    server = random.choice(servers)

    args = {
        'name': query,
        'order': 'votes',
        'offset': (params['pageno'] - 1) * number_of_results,
        'limit': number_of_results,
        'hidebroken': 'true',
        'reverse': 'true',
    }

    if 'language' in station_filters:
        lang = traits.get_language(params['searxng_locale'])  # type: ignore
        if lang:
            args['language'] = lang

    if 'countrycode' in station_filters:
        if len(params['searxng_locale'].split('-')) > 1:
            countrycode = params['searxng_locale'].split('-')[-1].upper()
            if countrycode in traits.custom['countrycodes']:  # type: ignore
                args['countrycode'] = countrycode

    params['url'] = f"{server}/json/stations/search?{urlencode(args)}"


def response(resp):
    results = []

    json_resp = resp.json()

    for result in json_resp:
        url = result['homepage']
        if not url:
            url = result['url_resolved']

        content = []
        tags = ', '.join(result.get('tags', '').split(','))
        if tags:
            content.append(tags)
        for x in ['state', 'country']:
            v = result.get(x)
            if v:
                v = str(v).strip()
                content.append(v)

        metadata = []
        codec = result.get('codec')
        if codec and codec.lower() != 'unknown':
            metadata.append(f'{codec} ' + gettext('radio'))
        for x, y in [
            (gettext('bitrate'), 'bitrate'),
            (gettext('votes'), 'votes'),
            (gettext('clicks'), 'clickcount'),
        ]:
            v = result.get(y)
            if v:
                v = str(v).strip()
                metadata.append(f"{x} {v}")
        results.append(
            {
                'url': url,
                'title': result['name'],
                'thumbnail': result.get('favicon', '').replace("http://", "https://"),
                'content': ' | '.join(content),
                'metadata': ' | '.join(metadata),
                'iframe_src': result['url_resolved'].replace("http://", "https://"),
            }
        )

    return results


def fetch_traits(engine_traits: EngineTraits):
    """Fetch languages and countrycodes from RadioBrowser

    - ``traits.languages``: `list of languages API`_
    - ``traits.custom['countrycodes']``: `list of countries API`_

    .. _list of countries API: https://de1.api.radio-browser.info/#List_of_countries
    .. _list of languages API: https://de1.api.radio-browser.info/#List_of_languages
    """
    # pylint: disable=import-outside-toplevel

    init(None)
    from babel.core import get_global

    babel_reg_list = get_global("territory_languages").keys()

    server = server_list()[0]
    language_list = get(f'{server}/json/languages').json()  # type: ignore
    country_list = get(f'{server}/json/countries').json()  # type: ignore

    for lang in language_list:

        babel_lang = lang.get('iso_639')
        if not babel_lang:
            # the language doesn't have any iso code, and hence can't be parsed
            # print(f"ERROR: lang - no iso code in {lang}")
            continue
        try:
            sxng_tag = language_tag(babel.Locale.parse(babel_lang, sep="-"))
        except babel.UnknownLocaleError:
            # print(f"ERROR: language tag {babel_lang} is unknown by babel")
            continue

        eng_tag = lang['name']
        conflict = engine_traits.languages.get(sxng_tag)
        if conflict:
            if conflict != eng_tag:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_tag, conflict, eng_tag))
            continue
        engine_traits.languages[sxng_tag] = eng_tag

    countrycodes = set()
    for region in country_list:
        # country_list contains duplicates that differ only in upper/lower case
        _reg = region['iso_3166_1'].upper()
        if _reg not in babel_reg_list:
            print(f"ERROR: region tag {region['iso_3166_1']} is unknown by babel")
            continue
        countrycodes.add(_reg)

    countrycodes = list(countrycodes)
    countrycodes.sort()
    engine_traits.custom['countrycodes'] = countrycodes
