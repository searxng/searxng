# SPDX-License-Identifier: AGPL-3.0-or-later
"""`Anna's Archive`_ is a free non-profit online shadow library metasearch
engine providing access to a variety of book resources (also via IPFS), created
by a team of anonymous archivists (AnnaArchivist_).

.. _Anna's Archive: https://annas-archive.org/
.. _AnnaArchivist: https://annas-software.org/AnnaArchivist/annas-archive

Configuration
=============

The engine has the following additional settings:

- :py:obj:`aa_content`
- :py:obj:`aa_ext`
- :py:obj:`aa_sort`

With this options a SearXNG maintainer is able to configure **additional**
engines for specific searches in Anna's Archive.  For example a engine to search
for *newest* articles and journals (PDF) / by shortcut ``!aaa <search-term>``.

.. code:: yaml

  - name: annas articles
    engine: annas_archive
    categories = ["general", "articles"]
    shortcut: aaa
    aa_content: "magazine"
    aa_ext: "pdf"
    aa_sort: "newest"


Implementations
===============

"""
import typing as t

from urllib.parse import urlencode
from lxml import html
from lxml.etree import ElementBase

from searx.utils import extract_text, eval_xpath, eval_xpath_getindex, eval_xpath_list
from searx.enginelib.traits import EngineTraits
from searx.data import ENGINE_TRAITS
from searx.exceptions import SearxEngineXPathException

from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

# about
about: dict[str, t.Any] = {
    "website": "https://annas-archive.org/",
    "wikidata_id": "Q115288326",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

# engine dependent config
categories = ["files", "books"]
paging: bool = True

# search-url
base_url: str = "https://annas-archive.org"
aa_content: str = ""
"""Anan's search form field **Content** / possible values::

    book_fiction, book_unknown, book_nonfiction,
    book_comic, magazine, standards_document

To not filter use an empty string (default).
"""
aa_sort: str = ""
"""Sort Anna's results, possible values::

    newest, oldest, largest, smallest

To sort by *most relevant* use an empty string (default)."""

aa_ext: str = ""
"""Filter Anna's results by a file ending.  Common filters for example are
``pdf`` and ``epub``.

.. note::

   Anna's Archive is a beta release: Filter results by file extension does not
   really work on Anna's Archive.

"""


def setup(engine_settings: dict[str, t.Any]) -> bool:  # pylint: disable=unused-argument
    """Check of engine's settings."""
    traits = EngineTraits(**ENGINE_TRAITS["annas archive"])

    if aa_content and aa_content not in traits.custom["content"]:
        raise ValueError(f"invalid setting content: {aa_content}")

    if aa_sort and aa_sort not in traits.custom["sort"]:
        raise ValueError(f"invalid setting sort: {aa_sort}")

    if aa_ext and aa_ext not in traits.custom["ext"]:
        raise ValueError(f"invalid setting ext: {aa_ext}")

    return True


def request(query: str, params: "OnlineParams") -> None:
    lang = traits.get_language(params["searxng_locale"], traits.all_locale)
    args = {
        "lang": lang,
        "content": aa_content,
        "ext": aa_ext,
        "sort": aa_sort,
        "q": query,
        "page": params["pageno"],
    }
    # filter out None and empty values
    filtered_args = dict((k, v) for k, v in args.items() if v)
    params["url"] = f"{base_url}/search?{urlencode(filtered_args)}"


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()
    dom = html.fromstring(resp.text)

    # The rendering of the WEB page is strange; positions of Anna's result page
    # are enclosed in SGML comments.  These comments are *uncommented* by some
    # JS code, see query of class ".js-scroll-hidden" in Anna's HTML template:
    #   https://annas-software.org/AnnaArchivist/annas-archive/-/blob/main/allthethings/templates/macros/md5_list.html

    for item in eval_xpath_list(dom, "//main//div[contains(@class, 'js-aarecord-list-outer')]/div"):
        try:
            kwargs: dict[str, t.Any] = _get_result(item)
        except SearxEngineXPathException:
            continue
        res.add(res.types.Paper(**kwargs))
    return res


def _get_result(item: ElementBase) -> dict[str, t.Any]:
    return {
        "url": base_url + eval_xpath_getindex(item, "./a/@href", 0),
        "title": extract_text(eval_xpath(item, "./div//a[starts-with(@href, '/md5')]")),
        "authors": [extract_text(eval_xpath_getindex(item, ".//a[starts-with(@href, '/search')]", 0))],
        "publisher": extract_text(
            eval_xpath_getindex(item, ".//a[starts-with(@href, '/search')]", 1, default=None), allow_none=True
        ),
        "content": extract_text(eval_xpath(item, ".//div[contains(@class, 'relative')]")),
        "thumbnail": extract_text(eval_xpath_getindex(item, ".//img/@src", 0, default=None), allow_none=True),
    }


def fetch_traits(engine_traits: EngineTraits):
    """Fetch languages and other search arguments from Anna's search form."""
    # pylint: disable=import-outside-toplevel

    import babel
    from searx.network import get  # see https://github.com/searxng/searxng/issues/762
    from searx.locales import language_tag

    engine_traits.all_locale = ""
    engine_traits.custom["content"] = []
    engine_traits.custom["ext"] = []
    engine_traits.custom["sort"] = []

    resp = get(base_url + "/search")
    if not resp.ok:
        raise RuntimeError("Response from Anna's search page is not OK.")
    dom = html.fromstring(resp.text)

    # supported language codes

    lang_map: dict[str, str] = {}
    for x in eval_xpath_list(dom, "//form//input[@name='lang']"):
        eng_lang = x.get("value")
        if eng_lang in ("", "_empty", "nl-BE", "und") or eng_lang.startswith("anti__"):
            continue
        try:
            locale = babel.Locale.parse(lang_map.get(eng_lang, eng_lang), sep="-")
        except babel.UnknownLocaleError:
            # silently ignore unknown languages
            # print("ERROR: %s -> %s is unknown by babel" % (x.get("data-name"), eng_lang))
            continue
        sxng_lang = language_tag(locale)
        conflict = engine_traits.languages.get(sxng_lang)
        if conflict:
            if conflict != eng_lang:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_lang, conflict, eng_lang))
            continue
        engine_traits.languages[sxng_lang] = eng_lang

    for x in eval_xpath_list(dom, "//form//input[@name='content']"):
        if not x.get("value").startswith("anti__"):
            engine_traits.custom["content"].append(x.get("value"))

    for x in eval_xpath_list(dom, "//form//input[@name='ext']"):
        if not x.get("value").startswith("anti__"):
            engine_traits.custom["ext"].append(x.get("value"))

    for x in eval_xpath_list(dom, "//form//select[@name='sort']//option"):
        engine_traits.custom["sort"].append(x.get("value"))

    # for better diff; sort the persistence of these traits
    engine_traits.custom["content"].sort()
    engine_traits.custom["ext"].sort()
    engine_traits.custom["sort"].sort()
