# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""This module implements the Wikipedia engine.  Some of this implementations
are shared by other engines:

- :ref:`wikidata engine`

The list of supported languages is fetched from the article linked by
:py:obj:`wikipedia_article_depth`.  Unlike traditional search engines, wikipedia
does not support one Wikipedia for all the languages, but there is one Wikipedia
for every language (:py:obj:`fetch_traits`).
"""

import urllib.parse
import babel

from lxml import html

from searx import network
from searx.locales import language_tag
from searx.enginelib.traits import EngineTraits

traits: EngineTraits

# about
about = {
    "website": 'https://www.wikipedia.org/',
    "wikidata_id": 'Q52',
    "official_api_documentation": 'https://en.wikipedia.org/api/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

send_accept_language_header = True

wikipedia_article_depth = 'https://meta.wikimedia.org/wiki/Wikipedia_article_depth'
"""The *editing depth* of Wikipedia is one of several possible rough indicators
of the encyclopedia's collaborative quality, showing how frequently its articles
are updated.  The measurement of depth was introduced after some limitations of
the classic measurement of article count were realized.
"""

# example: https://zh-classical.wikipedia.org/api/rest_v1/page/summary/日
rest_v1_summary_url = 'https://{wiki_netloc}/api/rest_v1/page/summary/{title}'
"""`wikipedia rest_v1 summary API`_: The summary response includes an extract of
the first paragraph of the page in plain text and HTML as well as the type of
page. This is useful for page previews (fka. Hovercards, aka. Popups) on the web
and link previews in the apps.

.. _wikipedia rest_v1 summary API: https://en.wikipedia.org/api/rest_v1/#/Page%20content/get_page_summary__title_

"""


def request(query, params):
    """Assemble a request (`wikipedia rest_v1 summary API`_)."""
    if query.islower():
        query = query.title()

    engine_language = traits.get_language(params['searxng_locale'], 'en')
    wiki_netloc = traits.custom['wiki_netloc'].get(engine_language, 'https://en.wikipedia.org/wiki/')
    title = urllib.parse.quote(query)

    # '!wikipedia 日 :zh-TW' --> https://zh-classical.wikipedia.org/
    # '!wikipedia 日 :zh' --> https://zh.wikipedia.org/
    params['url'] = rest_v1_summary_url.format(wiki_netloc=wiki_netloc, title=title)

    params['raise_for_httperror'] = False
    params['soft_max_redirects'] = 2

    return params


# get response from search-request
def response(resp):

    results = []
    if resp.status_code == 404:
        return []
    if resp.status_code == 400:
        try:
            api_result = resp.json()
        except Exception:  # pylint: disable=broad-except
            pass
        else:
            if (
                api_result['type'] == 'https://mediawiki.org/wiki/HyperSwitch/errors/bad_request'
                and api_result['detail'] == 'title-invalid-characters'
            ):
                return []

    network.raise_for_httperror(resp)

    api_result = resp.json()
    title = api_result['title']
    wikipedia_link = api_result['content_urls']['desktop']['page']
    results.append({'url': wikipedia_link, 'title': title, 'content': api_result.get('description', '')})

    if api_result.get('type') == 'standard':
        results.append(
            {
                'infobox': title,
                'id': wikipedia_link,
                'content': api_result.get('extract', ''),
                'img_src': api_result.get('thumbnail', {}).get('source'),
                'urls': [{'title': 'Wikipedia', 'url': wikipedia_link}],
            }
        )

    return results


# Nonstandard language codes
#
# These Wikipedias use language codes that do not conform to the ISO 639
# standard (which is how wiki subdomains are chosen nowadays).

lang_map = {
    'be-tarask': 'bel',
    'ak': 'aka',
    'als': 'gsw',
    'bat-smg': 'sgs',
    'cbk-zam': 'cbk',
    'fiu-vro': 'vro',
    'map-bms': 'map',
    'nrm': 'nrf',
    'roa-rup': 'rup',
    'nds-nl': 'nds',
    #'simple: – invented code used for the Simple English Wikipedia (not the official IETF code en-simple)
    'zh-min-nan': 'nan',
    'zh-yue': 'yue',
    'an': 'arg',
    'zh-classical': 'zh-Hant',  # babel maps classical to zh-Hans (for whatever reason)
}

unknown_langs = [
    'an',  # Aragonese
    'ba',  # Bashkir
    'bar',  # Bavarian
    'bcl',  # Central Bicolano
    'be-tarask',  # Belarusian variant / Belarusian is already covered by 'be'
    'bpy',  # Bishnupriya Manipuri is unknown by babel
    'hif',  # Fiji Hindi
    'ilo',  # Ilokano
    'li',  # Limburgish
    'sco',  # Scots (sco) is not known by babel, Scottish Gaelic (gd) is known by babel
    'sh',  # Serbo-Croatian
    'simple',  # simple english is not know as a natural language different to english (babel)
    'vo',  # Volapük
    'wa',  # Walloon
]


def fetch_traits(engine_traits: EngineTraits):
    """Fetch languages from Wikipedia.

    The location of the Wikipedia address of a language is mapped in a
    :py:obj:`custom field <searx.enginelib.traits.EngineTraits.custom>`
    (``wiki_netloc``).  Here is a reduced example:

    .. code:: python

       traits.custom['wiki_netloc'] = {
           "en": "en.wikipedia.org",
           ..
           "gsw": "als.wikipedia.org",
           ..
           "zh": "zh.wikipedia.org",
           "zh-classical": "zh-classical.wikipedia.org"
       }

    """

    engine_traits.custom['wiki_netloc'] = {}

    # insert alias to map from a region like zh-CN to a language zh_Hans
    engine_traits.languages['zh_Hans'] = 'zh'

    resp = network.get(wikipedia_article_depth)
    if not resp.ok:
        print("ERROR: response from Wikipedia is not OK.")

    dom = html.fromstring(resp.text)
    for row in dom.xpath('//table[contains(@class,"sortable")]//tbody/tr'):

        cols = row.xpath('./td')
        if not cols:
            continue
        cols = [c.text_content().strip() for c in cols]

        depth = float(cols[3].replace('-', '0').replace(',', ''))
        articles = int(cols[4].replace(',', '').replace(',', ''))

        if articles < 10000:
            # exclude languages with too few articles
            continue

        if int(depth) < 20:
            # Rough indicator of a Wikipedia’s quality, showing how frequently
            # its articles are updated.
            continue

        eng_tag = cols[2]
        wiki_url = row.xpath('./td[3]/a/@href')[0]
        wiki_url = urllib.parse.urlparse(wiki_url)

        if eng_tag in unknown_langs:
            continue

        try:
            sxng_tag = language_tag(babel.Locale.parse(lang_map.get(eng_tag, eng_tag), sep='-'))
        except babel.UnknownLocaleError:
            print("ERROR: %s [%s] is unknown by babel" % (cols[0], eng_tag))
            continue

        conflict = engine_traits.languages.get(sxng_tag)
        if conflict:
            if conflict != eng_tag:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_tag, conflict, eng_tag))
            continue

        engine_traits.languages[sxng_tag] = eng_tag
        engine_traits.custom['wiki_netloc'][eng_tag] = wiki_url.netloc
