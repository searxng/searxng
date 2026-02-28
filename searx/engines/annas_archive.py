# SPDX-License-Identifier: AGPL-3.0-or-later
"""`Anna's Archive`_ is a free non-profit online shadow library metasearch
engine providing access to a variety of book resources (also via IPFS), created
by a team of anonymous archivists (AnnaArchivist_).

.. _Anna's Archive: https://annas-archive.li/
.. _AnnaArchivist: https://software.annas-archive.li/AnnaArchivist/annas-archive

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

import random
import typing as t
from urllib.parse import urlencode

from lxml import html
from lxml.etree import ElementBase

from searx.data import ENGINE_TRAITS
from searx.enginelib.traits import EngineTraits
from searx.result_types import EngineResults
from searx.utils import eval_xpath, eval_xpath_getindex, eval_xpath_list, extract_text

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

# about
about: dict[str, t.Any] = {
    "website": "https://annas-archive.li/",
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
base_url: list[str] | str = []
"""List of Anna's archive domains or a single domain (as string)."""

aa_content: str = ""
"""Anan's search form field **Content** / possible values::

    book_fiction, book_unknown, book_nonfiction,
    book_comic, magazine, standards_document

To not filter use an empty string (default).
"""
aa_sort: str = ""
"""Sort Anna's results, possible values::

    newest, oldest, largest, smallest, newest_added, oldest_added, random

To sort by *most relevant* use an empty string (default)."""

aa_ext: str = ""
"""Filter Anna's results by a file ending.  Common filters for example are
``pdf`` and ``epub``.

.. note::

   Anna's Archive is a beta release: Filter results by file extension does not
   really work on Anna's Archive.

"""


def setup(_engine_settings: dict[str, t.Any]) -> bool:
    """Check of engine's settings."""

    traits: EngineTraits = EngineTraits(**ENGINE_TRAITS["annas archive"])

    if not base_url:
        raise ValueError("missing required config `base_url`")

    if aa_content and aa_content not in traits.custom["content"]:
        raise ValueError(f"invalid setting content: {aa_content}")

    if aa_sort and aa_sort not in traits.custom["sort"]:
        raise ValueError(f"invalid setting sort: {aa_sort}")

    if aa_ext and aa_ext not in traits.custom["ext"]:
        raise ValueError(f"invalid setting ext: {aa_ext}")

    return True


def _get_base_url_choice() -> str:
    if isinstance(base_url, list):
        return random.choice(base_url)

    return base_url


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
    # filter out empty values
    filtered_args = dict((k, v) for k, v in args.items() if v)

    params["base_url"] = _get_base_url_choice()
    params["url"] = f"{params['base_url']}/search?{urlencode(filtered_args)}"


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()
    dom = html.fromstring(resp.text)

    # Each result is a div with class "flex" inside "js-aarecord-list-outer"
    # container.  The "flex" filter excludes non-result div such as section
    # separators.
    for item in eval_xpath_list(
        dom,
        "//main//div[contains(@class, 'js-aarecord-list-outer')]/div[contains(@class, 'flex')]",
    ):
        result = _get_result(item, resp.search_params["base_url"])
        if result is not None:
            res.add(res.types.Paper(**result))

    return res


def _get_result(item: ElementBase, base_url_choice: str) -> dict[str, t.Any] | None:
    # the first direct child "a" contains the link to the result page
    href_els = item.xpath("./a/@href")
    if not href_els:
        return None

    # the link with class "js-vim-focus" is always the title link
    title_text = extract_text(
        xpath_results=eval_xpath(item, ".//a[contains(@class, 'js-vim-focus')]"),
        allow_none=True,
    )
    if not title_text:
        return None

    result: dict[str, t.Any] = {
        "url": base_url_choice + href_els[0],
        "title": title_text,
    }

    result["content"] = extract_text(
        xpath_results=eval_xpath_getindex(
            element=item,
            # the content is in a div with class "relative" and "line-clamp"
            xpath_spec=".//div[@class='relative']/div[contains(@class, 'line-clamp')]",
            index=0,
            default=None,
        ),
        allow_none=True,
    )

    result["thumbnail"] = eval_xpath_getindex(
        element=item,
        # the thumbnail is the src of the first img in the result item
        xpath_spec=".//img/@src",
        index=0,
        default=None,
    )

    result["authors"] = [
        extract_text(
            xpath_results=eval_xpath_getindex(
                element=item,
                # identified by the "user-edit" icon
                xpath_spec=".//a[.//span[contains(@class, 'icon-[mdi--user-edit]')]]",
                index=0,
                default=None,
            ),
            allow_none=True,
        )
    ]

    result["publisher"] = extract_text(
        xpath_results=eval_xpath_getindex(
            element=item,
            # identified by the "company" icon
            xpath_spec=".//a[.//span[contains(@class, 'icon-[mdi--company]')]]",
            index=0,
            default=None,
        ),
        allow_none=True,
    )

    tags_text = extract_text(
        xpath_results=eval_xpath_getindex(
            element=item,
            # the only one with "font-semibold" class
            xpath_spec=".//div[contains(@class, 'font-semibold')]",
            index=0,
            default=None,
        ),
        allow_none=True,
    )
    if tags_text:
        result["tags"] = [tag.strip() for tag in tags_text.split("Save")[0].split("·") if tag.strip()]

    return result


def fetch_traits(engine_traits: EngineTraits) -> None:
    """Fetch languages and other search arguments from Anna's search form."""
    # pylint: disable=import-outside-toplevel

    import babel

    from searx.locales import language_tag
    from searx.network import get  # see https://github.com/searxng/searxng/issues/762

    engine_traits.all_locale = ""
    engine_traits.custom["content"] = []
    engine_traits.custom["ext"] = []
    engine_traits.custom["sort"] = []

    resp = get(_get_base_url_choice() + "/search")
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
