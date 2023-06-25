# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""
Arch Linux Wiki
~~~~~~~~~~~~~~~

This implementation does not use a official API: Mediawiki provides API, but
Arch Wiki blocks access to it.

"""

from typing import TYPE_CHECKING
from urllib.parse import urlencode, urljoin, urlparse
import lxml
import babel

from searx.utils import extract_text, eval_xpath_list, eval_xpath_getindex
from searx.enginelib.traits import EngineTraits
from searx.locales import language_tag

if TYPE_CHECKING:
    import logging

    logger: logging.Logger

traits: EngineTraits


about = {
    "website": 'https://wiki.archlinux.org/',
    "wikidata_id": 'Q101445877',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['it', 'software wikis']
paging = True
main_wiki = 'wiki.archlinux.org'


def request(query, params):

    sxng_lang = params['searxng_locale'].split('-')[0]
    netloc: str = traits.custom['wiki_netloc'].get(sxng_lang, main_wiki)  # type: ignore
    title: str = traits.custom['title'].get(sxng_lang, 'Special:Search')  # type: ignore
    base_url = 'https://' + netloc + '/index.php?'
    offset = (params['pageno'] - 1) * 20

    if netloc == main_wiki:
        eng_lang: str = traits.get_language(sxng_lang, 'English')  # type: ignore
        query += ' (' + eng_lang + ')'
    elif netloc == 'wiki.archlinuxcn.org':
        base_url = 'https://' + netloc + '/wzh/index.php?'

    args = {
        'search': query,
        'title': title,
        'limit': 20,
        'offset': offset,
        'profile': 'default',
    }

    params['url'] = base_url + urlencode(args)
    return params


def response(resp):

    results = []
    dom = lxml.html.fromstring(resp.text)  # type: ignore

    # get the base URL for the language in which request was made
    sxng_lang = resp.search_params['searxng_locale'].split('-')[0]
    netloc: str = traits.custom['wiki_netloc'].get(sxng_lang, main_wiki)  # type: ignore
    base_url = 'https://' + netloc + '/index.php?'

    for result in eval_xpath_list(dom, '//ul[@class="mw-search-results"]/li'):
        link = eval_xpath_getindex(result, './/div[@class="mw-search-result-heading"]/a', 0)
        content = extract_text(result.xpath('.//div[@class="searchresult"]'))
        results.append(
            {
                'url': urljoin(base_url, link.get('href')),  # type: ignore
                'title': extract_text(link),
                'content': content,
            }
        )

    return results


def fetch_traits(engine_traits: EngineTraits):
    """Fetch languages from Archlinix-Wiki.  The location of the Wiki address of a
    language is mapped in a :py:obj:`custom field
    <searx.enginelib.traits.EngineTraits.custom>` (``wiki_netloc``).  Depending
    on the location, the ``title`` argument in the request is translated.

    .. code:: python

       "custom": {
         "wiki_netloc": {
           "de": "wiki.archlinux.de",
            # ...
           "zh": "wiki.archlinuxcn.org"
         }
         "title": {
           "de": "Spezial:Suche",
            # ...
           "zh": "Special:\u641c\u7d22"
         },
       },

    """
    # pylint: disable=import-outside-toplevel
    from searx.network import get  # see https://github.com/searxng/searxng/issues/762

    engine_traits.custom['wiki_netloc'] = {}
    engine_traits.custom['title'] = {}

    title_map = {
        'de': 'Spezial:Suche',
        'fa': 'ویژه:جستجو',
        'ja': '特別:検索',
        'zh': 'Special:搜索',
    }

    resp = get('https://wiki.archlinux.org/')
    if not resp.ok:  # type: ignore
        print("ERROR: response from wiki.archlinix.org is not OK.")

    dom = lxml.html.fromstring(resp.text)  # type: ignore
    for a in eval_xpath_list(dom, "//a[@class='interlanguage-link-target']"):

        sxng_tag = language_tag(babel.Locale.parse(a.get('lang'), sep='-'))
        # zh_Hans --> zh
        sxng_tag = sxng_tag.split('_')[0]

        netloc = urlparse(a.get('href')).netloc
        if netloc != 'wiki.archlinux.org':
            title = title_map.get(sxng_tag)
            if not title:
                print("ERROR: title tag from %s (%s) is unknown" % (netloc, sxng_tag))
                continue
            engine_traits.custom['wiki_netloc'][sxng_tag] = netloc
            engine_traits.custom['title'][sxng_tag] = title  # type: ignore

        eng_tag = extract_text(eval_xpath_list(a, ".//span"))
        engine_traits.languages[sxng_tag] = eng_tag  # type: ignore

    engine_traits.languages['en'] = 'English'
