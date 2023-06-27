# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Anna's Archive

"""
from typing import List, Dict, Any, Optional
from urllib.parse import quote
from lxml import html

from searx.utils import extract_text, eval_xpath, eval_xpath_list
from searx.enginelib.traits import EngineTraits

# about
about: Dict[str, Any] = {
    "website": "https://annas-archive.org/",
    "wikidata_id": "Q115288326",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

# engine dependent config
categories: List[str] = ["files"]
paging: bool = False

# search-url
base_url: str = "https://annas-archive.org"

# xpath queries
xpath_results: str = '//main//a[starts-with(@href,"/md5")]'
xpath_url: str = ".//@href"
xpath_title: str = ".//h3/text()[1]"
xpath_authors: str = './/div[contains(@class, "italic")]'
xpath_publisher: str = './/div[contains(@class, "text-sm")]'
xpath_file_info: str = './/div[contains(@class, "text-xs")]'


def request(query, params: Dict[str, Any]) -> Dict[str, Any]:
    search_url: str = base_url + "/search?q={search_query}&lang={lang}"
    lang: str = ""
    if params["language"] != "all":
        lang = params["language"]

    params["url"] = search_url.format(search_query=quote(query), lang=lang)
    return params


def response(resp) -> List[Dict[str, Optional[str]]]:
    results: List[Dict[str, Optional[str]]] = []
    dom = html.fromstring(resp.text)

    for item in dom.xpath(xpath_results):
        result: Dict[str, Optional[str]] = {}

        result["url"] = base_url + item.xpath(xpath_url)[0]

        result["title"] = extract_text(eval_xpath(item, xpath_title))

        result["content"] = "{publisher}. {authors}. {file_info}".format(
            authors=extract_text(eval_xpath(item, xpath_authors)),
            publisher=extract_text(eval_xpath(item, xpath_publisher)),
            file_info=extract_text(eval_xpath(item, xpath_file_info)),
        )

        results.append(result)

    return results


def fetch_traits(engine_traits: EngineTraits):
    """Fetch languages and other search arguments from Anna's search form."""
    # pylint: disable=import-outside-toplevel

    import babel
    from searx.network import get  # see https://github.com/searxng/searxng/issues/762
    from searx.locales import language_tag

    engine_traits.all_locale = ''
    engine_traits.custom['content'] = []
    engine_traits.custom['ext'] = []
    engine_traits.custom['sort'] = []

    resp = get(base_url + '/search')
    if not resp.ok:  # type: ignore
        raise RuntimeError("Response from Anna's search page is not OK.")
    dom = html.fromstring(resp.text)  # type: ignore

    # supported language codes

    lang_map = {}
    for x in eval_xpath_list(dom, "//form//select[@name='lang']//option"):
        eng_lang = x.get("value")
        if eng_lang in ('', '_empty', 'nl-BE', 'und'):
            continue
        try:
            locale = babel.Locale.parse(lang_map.get(eng_lang, eng_lang), sep='-')
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

    for x in eval_xpath_list(dom, "//form//select[@name='content']//option"):
        engine_traits.custom['content'].append(x.get("value"))

    for x in eval_xpath_list(dom, "//form//select[@name='ext']//option"):
        engine_traits.custom['ext'].append(x.get("value"))

    for x in eval_xpath_list(dom, "//form//select[@name='sort']//option"):
        engine_traits.custom['sort'].append(x.get("value"))
