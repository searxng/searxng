# SPDX-License-Identifier: AGPL-3.0-or-later
"""Privacywall_ claims to be a "privacy-friendly" search engine,
but according to a `Privacyguides discussion`_ it's sharing private
user information with Microsoft and Amazon.

.. _Privacywall : https://www.privacywall.org
.. _`Privacyguides discussion` : https://discuss.privacyguides.net/t/how-is-privacy-wall-search-engine/29486
"""

import typing as t
from urllib.parse import urlencode, unquote_plus

from lxml import html
import babel

from searx.enginelib.traits import EngineTraits
from searx.utils import eval_xpath_list, eval_xpath, extract_text, get_embeded_stream_url, extr
from searx.locales import region_tag
from searx.result_types import EngineResults


if t.TYPE_CHECKING:
    from lxml.etree import ElementBase
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://privacywall.org",
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

paging = True
safesearch = True
time_range_support = True

base_url = "https://www.privacywall.org"
privacywall_category = "general"
"""Supported categories are ``general``, ``videos`` and ``images``."""


# corresponds to the "k" query param
safesearch_map = {0: "off", 1: "on", 2: "on"}

# page number sent for videos (is independent of the query) - certainly there's
# a pattern in this, but for our use case it's enough to just support the first
# 10 pages by hardcoding the page "numbers"
video_page_map = {
    2: "CAoQAA",
    3: "CBQQAA",
    4: "CB4QAA",
    5: "CCgQAA",
    6: "CDIQAA",
    7: "CDwQAA",
    8: "CEYQAA",
    9: "CFAQAA",
    10: "CFoQAA",
}


def init(_):
    if privacywall_category not in ("general", "images", "videos"):
        raise ValueError("invalid category: %s" % privacywall_category)


def request(query: str, params: "OnlineParams") -> None:
    if params["pageno"] > 10:
        params["url"] = None
        return

    args = {"q": query, "safesearch": safesearch_map[params["safesearch"]]}
    if params["searxng_locale"] != "all":
        args["cc"] = traits.get_region(params["searxng_locale"]) or "US"
    if params["time_range"]:
        # time range uses the same "day", "week", "month", "year" naming scheme as SearXNG
        args["time"] = params["time_range"]

    if params["pageno"] > 1:
        if privacywall_category == "images":
            args["page"] = str(params["pageno"])
        elif privacywall_category == "videos":
            args["page"] = video_page_map[params["pageno"]]
        else:
            raise ValueError("general engine does not support pagination")

    if privacywall_category == "general":
        params["url"] = f"{base_url}/search/secure/?{urlencode(args)}"
    else:
        params["url"] = f"{base_url}/{privacywall_category}/?{urlencode(args)}"


def _general_results(doc: "ElementBase") -> EngineResults:
    res = EngineResults()
    for result in eval_xpath_list(doc, "//div[@id='pw-results-main']/div[contains(@class, 'result-card')]"):
        (
            res.add(
                res.types.MainResult(
                    url=extract_text(eval_xpath(result, ".//a[contains(@class, 'result-url-anchor')]/@href")) or "",
                    title=extract_text(eval_xpath(result, ".//div[contains(@class, 'result_title')]")) or "",
                    content=extract_text(eval_xpath(result, ".//div[contains(@class, 'result-description')]")) or "",
                ),
            )
        )
    return res


def _extract_thumbnail_url(url: str) -> str:
    """
    Get the URL from strings like "/videos/video.php?id=<urlencoded-urlhere>".
    """
    url_start = url.find("?id=") + len("?id=")
    thumbnail = unquote_plus(url[url_start:])
    return thumbnail


def _image_results(doc: "ElementBase") -> EngineResults:
    res = EngineResults()
    for result in eval_xpath_list(doc, "//div[@id='container']/div[contains(@class, 'imgcontainer')]"):
        (
            res.add(
                res.types.Image(
                    url=extract_text(eval_xpath(result, "./a/@href")) or "",
                    content=extract_text(eval_xpath(result, "./a/@alt")) or "",
                    thumbnail_src=_extract_thumbnail_url(extract_text(eval_xpath(result, ".//img/@src")) or ""),
                    source=extract_text(eval_xpath(result, ".//div[contains(@class, 'image-source-badge')]")) or "",
                ),
            )
        )
    return res


def _video_results(doc: "ElementBase") -> EngineResults:
    res = EngineResults()
    for result in eval_xpath_list(
        doc, "//div[contains(@class, 'video-container')]/div[contains(@class, 'video-card')]"
    ):
        url = extract_text(eval_xpath(result, "./a/@href")) or ""
        if not url:
            continue

        thumbnail = None
        # looks like <div style="background-image:url(/videos/video.php?id=<urlencoded-urlhere>);position:relative">
        thumbnail_style = extract_text(eval_xpath(result, ".//div[contains(@class, 'video-img')]/@style"))
        if thumbnail_style:
            thumbnail = _extract_thumbnail_url(extr(thumbnail_style, ":url(", ")"))

        res.add(
            res.types.LegacyResult(
                template="videos.html",
                url=url,
                title=extract_text(eval_xpath(result, ".//h2[contains(@class, 'video-card-title')]")) or "",
                content=extract_text(eval_xpath(result, ".//p")) or "",
                thumbnail=thumbnail or "",
                iframe_src=get_embeded_stream_url(url) or "",
            )
        )

    return res


def response(resp: "SXNG_Response") -> EngineResults:
    doc = html.fromstring(resp.text)
    match privacywall_category:
        case "general":
            return _general_results(doc)
        case "images":
            return _image_results(doc)
        case "videos":
            return _video_results(doc)
        case _:
            raise ValueError("invalid category: %s" % privacywall_category)


def fetch_traits(engine_traits: EngineTraits) -> None:
    """Fetch regions from Bing-Web."""
    # pylint: disable=import-outside-toplevel

    from searx.network import get  # see https://github.com/searxng/searxng/issues/762
    from searx.utils import gen_useragent

    headers = {
        "User-Agent": gen_useragent(),
    }

    resp = get(base_url, headers=headers)
    if not resp.ok:
        raise RuntimeError("Response from Privacywall is not OK.")

    dom = html.fromstring(resp.text)

    # <div class="dropdown-option" onclick="changeMenuLanguage(&quot;CZ&quot;)"></div>
    for onclick_listener in eval_xpath(
        dom, "//div[contains(@class, 'lang-menu')]//div[contains(@class, 'dropdown-option')]/@onclick"
    ):
        # this is either a normal lang-country tag (e.g. cs-cz) or only a country code (e.g. de, at, ...)
        country_tag = extr(onclick_listener, "(\"", "\")")

        # the locale tag is only a country tag, so we get languages the from the list of official languages
        # of the country
        lang_tag: str
        for lang_tag in babel.languages.get_official_languages(country_tag, de_facto=True):  # pyright: ignore
            try:
                sxng_tag = region_tag(babel.Locale.parse(f"{lang_tag}_{country_tag.upper()}"))
            except babel.UnknownLocaleError:
                # silently ignore unknown languages
                continue

            conflict = engine_traits.regions.get(sxng_tag)
            if conflict:
                if conflict != sxng_tag:
                    print("CONFLICT: babel %s --> %s" % (sxng_tag, conflict))
                continue

            engine_traits.regions[sxng_tag] = country_tag
