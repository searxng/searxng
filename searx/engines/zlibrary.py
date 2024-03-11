# SPDX-License-Identifier: AGPL-3.0-or-later
"""`Z-Library`_ (abbreviated as z-lib, formerly BookFinder) is a shadow library
project for file-sharing access to scholarly journal articles, academic texts
and general-interest books.  It began as a mirror of Library Genesis, from which
most of its books originate.

.. _Z-Library: https://zlibrary-global.se/

Configuration
=============

The engine has the following additional settings:

- :py:obj:`zlib_year_from`
- :py:obj:`zlib_year_to`
- :py:obj:`zlib_ext`

With this options a SearXNG maintainer is able to configure **additional**
engines for specific searches in Z-Library.  For example a engine to search
only for EPUB from 2010 to 2020.

.. code:: yaml

   - name: z-library 2010s epub
     engine: zlibrary
     shortcut: zlib2010s
     zlib_year_from: '2010'
     zlib_year_to: '2020'
     zlib_ext: 'EPUB'

Implementations
===============

"""
from __future__ import annotations
from typing import TYPE_CHECKING
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import quote
from lxml import html
from flask_babel import gettext

from searx.utils import extract_text, eval_xpath, eval_xpath_list
from searx.enginelib.traits import EngineTraits
from searx.data import ENGINE_TRAITS

if TYPE_CHECKING:
    import httpx
    import logging

    logger: logging.Logger

# about
about: Dict[str, Any] = {
    "website": "https://zlibrary-global.se",
    "wikidata_id": "Q104863992",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

categories: List[str] = ["files"]
paging: bool = True
base_url: str = "https://zlibrary-global.se"

zlib_year_from: str = ""
"""Filter z-library's results by year from. E.g '2010'.
"""

zlib_year_to: str = ""
"""Filter z-library's results by year to. E.g. '2010'.
"""

zlib_ext: str = ""
"""Filter z-library's results by a file ending. Common filters for example are
``PDF`` and ``EPUB``.
"""


def init(engine_settings=None) -> None:  # pylint: disable=unused-argument
    """Check of engine's settings."""
    traits: EngineTraits = EngineTraits(**ENGINE_TRAITS["z-library"])

    if zlib_ext and zlib_ext not in traits.custom["ext"]:
        raise ValueError(f"invalid setting ext: {zlib_ext}")
    if zlib_year_from and zlib_year_from not in traits.custom["year_from"]:
        raise ValueError(f"invalid setting year_from: {zlib_year_from}")
    if zlib_year_to and zlib_year_to not in traits.custom["year_to"]:
        raise ValueError(f"invalid setting year_to: {zlib_year_to}")


def request(query: str, params: Dict[str, Any]) -> Dict[str, Any]:
    lang: str = traits.get_language(params["language"], traits.all_locale)  # type: ignore
    search_url: str = (
        base_url
        + "/s/{search_query}/?page={pageno}"
        + "&yearFrom={zlib_year_from}"
        + "&yearTo={zlib_year_to}"
        + "&languages[]={lang}"
        + "&extensions[]={zlib_ext}"
    )
    params["url"] = search_url.format(
        search_query=quote(query),
        pageno=params["pageno"],
        lang=lang,
        zlib_year_from=zlib_year_from,
        zlib_year_to=zlib_year_to,
        zlib_ext=zlib_ext,
    )
    return params


def response(resp: httpx.Response) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    dom = html.fromstring(resp.text)

    for item in dom.xpath('//div[@id="searchResultBox"]//div[contains(@class, "resItemBox")]'):
        results.append(_parse_result(item))

    return results


def _text(item, selector: str) -> str | None:
    return extract_text(eval_xpath(item, selector))


i18n_language = gettext("Language")
i18n_book_rating = gettext("Book rating")
i18n_file_quality = gettext("File quality")


def _parse_result(item) -> Dict[str, Any]:

    author_elements = eval_xpath_list(item, './/div[@class="authors"]//a[@itemprop="author"]')

    result = {
        "template": "paper.html",
        "url": base_url + item.xpath('(.//a[starts-with(@href, "/book/")])[1]/@href')[0],
        "title": _text(item, './/*[@itemprop="name"]'),
        "authors": [extract_text(author) for author in author_elements],
        "publisher": _text(item, './/a[@title="Publisher"]'),
        "type": _text(item, './/div[contains(@class, "property__file")]//div[contains(@class, "property_value")]'),
        "img_src": _text(item, './/img[contains(@class, "cover")]/@data-src'),
    }

    year = _text(item, './/div[contains(@class, "property_year")]//div[contains(@class, "property_value")]')
    if year:
        result["publishedDate"] = datetime.strptime(year, '%Y')

    content = []
    language = _text(item, './/div[contains(@class, "property_language")]//div[contains(@class, "property_value")]')
    if language:
        content.append(f"{i18n_language}: {language.capitalize()}")
    book_rating = _text(item, './/span[contains(@class, "book-rating-interest-score")]')
    if book_rating and float(book_rating):
        content.append(f"{i18n_book_rating}: {book_rating}")
    file_quality = _text(item, './/span[contains(@class, "book-rating-quality-score")]')
    if file_quality and float(file_quality):
        content.append(f"{i18n_file_quality}: {file_quality}")
    result["content"] = " | ".join(content)

    return result


def fetch_traits(engine_traits: EngineTraits) -> None:
    """Fetch languages and other search arguments from zlibrary's search form."""
    # pylint: disable=import-outside-toplevel

    import babel
    from searx.network import get  # see https://github.com/searxng/searxng/issues/762
    from searx.locales import language_tag

    engine_traits.all_locale = ""
    engine_traits.custom["ext"] = []
    engine_traits.custom["year_from"] = []
    engine_traits.custom["year_to"] = []

    resp = get(base_url)
    if not resp.ok:  # type: ignore
        raise RuntimeError("Response from zlibrary's search page is not OK.")
    dom = html.fromstring(resp.text)  # type: ignore

    for year in eval_xpath_list(dom, "//div[@id='advSearch-noJS']//select[@id='sf_yearFrom']/option"):
        engine_traits.custom["year_from"].append(year.get("value"))

    for year in eval_xpath_list(dom, "//div[@id='advSearch-noJS']//select[@id='sf_yearTo']/option"):
        engine_traits.custom["year_to"].append(year.get("value"))

    for ext in eval_xpath_list(dom, "//div[@id='advSearch-noJS']//select[@id='sf_extensions']/option"):
        value: Optional[str] = ext.get("value")
        if value is None:
            value = ""
        engine_traits.custom["ext"].append(value)

    # Handle languages
    # Z-library uses English names for languages, so we need to map them to their respective locales
    language_name_locale_map: Dict[str, babel.Locale] = {}
    for locale in babel.core.localedata.locale_identifiers():  # type: ignore
        # Create a Locale object for the current locale
        loc = babel.Locale.parse(locale)
        if loc.english_name is None:
            continue
        language_name_locale_map[loc.english_name.lower()] = loc  # type: ignore

    for x in eval_xpath_list(dom, "//div[@id='advSearch-noJS']//select[@id='sf_languages']/option"):
        eng_lang = x.get("value")
        if eng_lang is None:
            continue
        try:
            locale = language_name_locale_map[eng_lang.lower()]
        except KeyError:
            # silently ignore unknown languages
            # print("ERROR: %s is unknown by babel" % (eng_lang))
            continue
        sxng_lang = language_tag(locale)
        conflict = engine_traits.languages.get(sxng_lang)
        if conflict:
            if conflict != eng_lang:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_lang, conflict, eng_lang))
            continue
        engine_traits.languages[sxng_lang] = eng_lang
