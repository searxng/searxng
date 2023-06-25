# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""This module implements the Wikipedia engine.  Some of this implementations
are shared by other engines:

- :ref:`wikidata engine`

The list of supported languages is :py:obj:`fetched <fetch_wikimedia_traits>` from
the article linked by :py:obj:`list_of_wikipedias`.

Unlike traditional search engines, wikipedia does not support one Wikipedia for
all languages, but there is one Wikipedia for each supported language. Some of
these Wikipedias have a LanguageConverter_ enabled
(:py:obj:`rest_v1_summary_url`).

A LanguageConverter_ (LC) is a system based on language variants that
automatically converts the content of a page into a different variant. A variant
is mostly the same language in a different script.

- `Wikipedias in multiple writing systems`_
- `Automatic conversion between traditional and simplified Chinese characters`_

PR-2554_:
  The Wikipedia link returned by the API is still the same in all cases
  (`https://zh.wikipedia.org/wiki/出租車`_) but if your browser's
  ``Accept-Language`` is set to any of ``zh``, ``zh-CN``, ``zh-TW``, ``zh-HK``
  or .. Wikipedia's LC automatically returns the desired script in their
  web-page.

  - You can test the API here: https://reqbin.com/gesg2kvx

.. _https://zh.wikipedia.org/wiki/出租車:
   https://zh.wikipedia.org/wiki/%E5%87%BA%E7%A7%9F%E8%BB%8A

To support Wikipedia's LanguageConverter_, a SearXNG request to Wikipedia uses
:py:obj:`get_wiki_params` and :py:obj:`wiki_lc_locale_variants' in the
:py:obj:`fetch_wikimedia_traits` function.

To test in SearXNG, query for ``!wp 出租車`` with each of the available Chinese
options:

- ``!wp 出租車 :zh``    should show 出租車
- ``!wp 出租車 :zh-CN`` should show 出租车
- ``!wp 出租車 :zh-TW`` should show 計程車
- ``!wp 出租車 :zh-HK`` should show 的士
- ``!wp 出租車 :zh-SG`` should show 德士

.. _LanguageConverter:
   https://www.mediawiki.org/wiki/Writing_systems#LanguageConverter
.. _Wikipedias in multiple writing systems:
   https://meta.wikimedia.org/wiki/Wikipedias_in_multiple_writing_systems
.. _Automatic conversion between traditional and simplified Chinese characters:
   https://en.wikipedia.org/wiki/Chinese_Wikipedia#Automatic_conversion_between_traditional_and_simplified_Chinese_characters
.. _PR-2554: https://github.com/searx/searx/pull/2554

"""

import urllib.parse
import babel

from lxml import html

from searx import utils
from searx import network as _network
from searx import locales
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
"""The HTTP ``Accept-Language`` header is needed for wikis where
LanguageConverter_ is enabled."""

list_of_wikipedias = 'https://meta.wikimedia.org/wiki/List_of_Wikipedias'
"""`List of all wikipedias <https://meta.wikimedia.org/wiki/List_of_Wikipedias>`_
"""

wikipedia_article_depth = 'https://meta.wikimedia.org/wiki/Wikipedia_article_depth'
"""The *editing depth* of Wikipedia is one of several possible rough indicators
of the encyclopedia's collaborative quality, showing how frequently its articles
are updated.  The measurement of depth was introduced after some limitations of
the classic measurement of article count were realized.
"""

rest_v1_summary_url = 'https://{wiki_netloc}/api/rest_v1/page/summary/{title}'
"""
`wikipedia rest_v1 summary API`_:
  The summary response includes an extract of the first paragraph of the page in
  plain text and HTML as well as the type of page. This is useful for page
  previews (fka. Hovercards, aka. Popups) on the web and link previews in the
  apps.

HTTP ``Accept-Language`` header (:py:obj:`send_accept_language_header`):
  The desired language variant code for wikis where LanguageConverter_ is
  enabled.

.. _wikipedia rest_v1 summary API:
   https://en.wikipedia.org/api/rest_v1/#/Page%20content/get_page_summary__title_

"""

wiki_lc_locale_variants = {
    "zh": (
        "zh-CN",
        "zh-HK",
        "zh-MO",
        "zh-MY",
        "zh-SG",
        "zh-TW",
    ),
    "zh-classical": ("zh-classical",),
}
"""Mapping rule of the LanguageConverter_ to map a language and its variants to
a Locale (used in the HTTP ``Accept-Language`` header). For example see `LC
Chinese`_.

.. _LC Chinese:
   https://meta.wikimedia.org/wiki/Wikipedias_in_multiple_writing_systems#Chinese
"""

wikipedia_script_variants = {
    "zh": (
        "zh_Hant",
        "zh_Hans",
    )
}


def get_wiki_params(sxng_locale, eng_traits):
    """Returns the Wikipedia language tag and the netloc that fits to the
    ``sxng_locale``.  To support LanguageConverter_ this function rates a locale
    (region) higher than a language (compare :py:obj:`wiki_lc_locale_variants`).

    """
    eng_tag = eng_traits.get_region(sxng_locale, eng_traits.get_language(sxng_locale, 'en'))
    wiki_netloc = eng_traits.custom['wiki_netloc'].get(eng_tag, 'en.wikipedia.org')
    return eng_tag, wiki_netloc


def request(query, params):
    """Assemble a request (`wikipedia rest_v1 summary API`_)."""
    if query.islower():
        query = query.title()

    _eng_tag, wiki_netloc = get_wiki_params(params['searxng_locale'], traits)
    title = urllib.parse.quote(query)
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

    _network.raise_for_httperror(resp)

    api_result = resp.json()
    title = utils.html_to_text(api_result.get('titles', {}).get('display') or api_result.get('title'))
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

lang_map = locales.LOCALE_BEST_MATCH.copy()
lang_map.update(
    {
        'be-tarask': 'bel',
        'ak': 'aka',
        'als': 'gsw',
        'bat-smg': 'sgs',
        'cbk-zam': 'cbk',
        'fiu-vro': 'vro',
        'map-bms': 'map',
        'no': 'nb-NO',
        'nrm': 'nrf',
        'roa-rup': 'rup',
        'nds-nl': 'nds',
        #'simple: – invented code used for the Simple English Wikipedia (not the official IETF code en-simple)
        'zh-min-nan': 'nan',
        'zh-yue': 'yue',
        'an': 'arg',
    }
)


def fetch_traits(engine_traits: EngineTraits):
    fetch_wikimedia_traits(engine_traits)
    print("WIKIPEDIA_LANGUAGES: %s" % len(engine_traits.custom['WIKIPEDIA_LANGUAGES']))


def fetch_wikimedia_traits(engine_traits: EngineTraits):
    """Fetch languages from Wikipedia.  Not all languages from the
    :py:obj:`list_of_wikipedias` are supported by SearXNG locales, only those
    known from :py:obj:`searx.locales.LOCALE_NAMES` or those with a minimal
    :py:obj:`editing depth <wikipedia_article_depth>`.

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
    # pylint: disable=too-many-branches
    engine_traits.custom['wiki_netloc'] = {}
    engine_traits.custom['WIKIPEDIA_LANGUAGES'] = []

    # insert alias to map from a script or region to a wikipedia variant

    for eng_tag, sxng_tag_list in wikipedia_script_variants.items():
        for sxng_tag in sxng_tag_list:
            engine_traits.languages[sxng_tag] = eng_tag
    for eng_tag, sxng_tag_list in wiki_lc_locale_variants.items():
        for sxng_tag in sxng_tag_list:
            engine_traits.regions[sxng_tag] = eng_tag

    resp = _network.get(list_of_wikipedias)
    if not resp.ok:
        print("ERROR: response from Wikipedia is not OK.")

    dom = html.fromstring(resp.text)
    for row in dom.xpath('//table[contains(@class,"sortable")]//tbody/tr'):

        cols = row.xpath('./td')
        if not cols:
            continue
        cols = [c.text_content().strip() for c in cols]

        depth = float(cols[11].replace('-', '0').replace(',', ''))
        articles = int(cols[4].replace(',', '').replace(',', ''))

        eng_tag = cols[3]
        wiki_url = row.xpath('./td[4]/a/@href')[0]
        wiki_url = urllib.parse.urlparse(wiki_url)

        try:
            sxng_tag = locales.language_tag(babel.Locale.parse(lang_map.get(eng_tag, eng_tag), sep='-'))
        except babel.UnknownLocaleError:
            # print("ERROR: %s [%s] is unknown by babel" % (cols[0], eng_tag))
            continue
        finally:
            engine_traits.custom['WIKIPEDIA_LANGUAGES'].append(eng_tag)

        if sxng_tag not in locales.LOCALE_NAMES:

            if articles < 10000:
                # exclude languages with too few articles
                continue

            if int(depth) < 20:
                # Rough indicator of a Wikipedia’s quality, showing how
                # frequently its articles are updated.
                continue

        conflict = engine_traits.languages.get(sxng_tag)
        if conflict:
            if conflict != eng_tag:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_tag, conflict, eng_tag))
            continue

        engine_traits.languages[sxng_tag] = eng_tag
        engine_traits.custom['wiki_netloc'][eng_tag] = wiki_url.netloc

    engine_traits.custom['WIKIPEDIA_LANGUAGES'].sort()
