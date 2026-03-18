# SPDX-License-Identifier: AGPL-3.0-or-later
"""This is the implementation of the Bing-Web engine.  Some of this
implementations are shared by other engines:

- :ref:`bing images engine`
- :ref:`bing news engine`
- :ref:`bing videos engine`

.. note::

   Some functionality (paging and time-range results) are not supported
   since they depend on JavaScript.
"""

import base64
import re
import typing as t
from urllib.parse import parse_qs, urlencode, urlparse

import babel
import babel.languages
from lxml import html

from searx.enginelib.traits import EngineTraits
from searx.locales import region_tag
from searx.utils import eval_xpath, eval_xpath_getindex, eval_xpath_list, extract_text

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about: dict[str, t.Any] = {
    "website": "https://www.bing.com",
    "wikidata_id": "Q182496",
    "official_api_documentation": "https://github.com/MicrosoftDocs/bing-docs",
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

# engine dependent config
categories = ["general", "web"]
safesearch = True
_safesearch_map: dict[int, str] = {
    0: "off",
    1: "moderate",
    2: "strict",
}
"""Filter results. 0: None, 1: Moderate, 2: Strict"""

base_url = "https://www.bing.com/search"
"""Bing-Web search URL"""


def get_locale_params(engine_region: str | None) -> dict[str, str] | None:
    """API documentation states the ``mkt`` parameter is *the
    recommended primary signal* for locale:

        If known, you are encouraged to always specify the market.
        Specifying the market helps Bing route the request and return an
        appropriate and optimal response.

    The ``mkt`` parameter takes a full ``<language>-<country>`` code.

    This function is shared with :py:mod:`searx.engines.bing_images`,
    :py:mod:`searx.engines.bing_news`, and :py:mod:`searx.engines.bing_videos`.
    """

    if not engine_region or engine_region == "clear":
        return None

    return {"mkt": engine_region}


def override_accept_language(params: "OnlineParams", engine_region: str | None) -> None:
    """Override the ``Accept-Language`` header.

    The default header built by :py:class:`~searx.search.processors.online.OnlineProcessor`
    appends ``en;q=0.3`` as a fallback language::

        Accept-Language: de,de-DE;q=0.7,en;q=0.3

    Bing seems to better select the results locale based on the
    ``Accept-Language`` value header.

    This function is shared with :py:mod:`searx.engines.bing_images`,
    :py:mod:`searx.engines.bing_news`, and :py:mod:`searx.engines.bing_videos`.
    """

    if not engine_region or engine_region == "clear":
        return

    lang = engine_region.split("-")[0]
    params["headers"]["Accept-Language"] = f"{engine_region},{lang};q=0.9"


def request(query: str, params: "OnlineParams") -> "OnlineParams":
    """Assemble a Bing-Web request."""

    engine_region = traits.get_region(params["searxng_locale"], traits.all_locale)

    override_accept_language(params, engine_region)

    query_params: dict[str, str | int] = {
        "q": query,
        "adlt": _safesearch_map.get(params.get("safesearch", 0), "off"),
    }

    locale_params = get_locale_params(engine_region)
    if locale_params:
        query_params.update(locale_params)

    params["url"] = f"{base_url}?{urlencode(query_params)}"

    # in some regions where geoblocking is employed (e.g. China),
    # www.bing.com redirects to the regional version of Bing
    params["allow_redirects"] = True

    return params


def response(resp: "SXNG_Response") -> list[dict[str, t.Any]]:
    """Get response from Bing-Web"""

    results: list[dict[str, t.Any]] = []

    dom = html.fromstring(resp.text)

    for item in eval_xpath_list(dom, '//ol[@id="b_results"]/li[contains(@class, "b_algo")]'):
        link = eval_xpath_getindex(item, ".//h2/a", 0, None)
        if link is None:
            continue

        href = link.attrib.get("href", "")
        title = extract_text(link)

        if not href or not title:
            continue

        # what about cn.bing.com, ..?
        if href.startswith("https://www.bing.com/ck/a?"):
            qs = parse_qs(urlparse(href).query)
            u_values = qs.get("u")
            if u_values:
                u_val = u_values[0]
                if u_val.startswith("a1"):
                    encoded = u_val[2:]
                    # base64url without padding
                    encoded += "=" * (-len(encoded) % 4)
                    href = base64.urlsafe_b64decode(encoded).decode("utf-8", errors="replace")

        # remove decorative icons that Bing injects into <p> elements
        # (`<span class="algoSlug_icon">`)
        content_els = eval_xpath(item, ".//p")
        for p in content_els:
            for icon in p.xpath('.//span[@class="algoSlug_icon"]'):
                icon.getparent().remove(icon)
        content = extract_text(content_els)

        results.append({"url": href, "title": title, "content": content})

    if results:
        result_len_container = "".join(eval_xpath(dom, '//span[@class="sb_count"]//text()'))
        result_len_container = re.sub(r"[^0-9]", "", result_len_container)
        if result_len_container:
            results.append({"number_of_results": int(result_len_container)})

    return results


def fetch_traits(engine_traits: EngineTraits) -> None:
    """Fetch regions from Bing-Web."""
    # pylint: disable=import-outside-toplevel

    from searx.network import get  # see https://github.com/searxng/searxng/issues/762
    from searx.utils import gen_useragent

    headers = {
        "User-Agent": gen_useragent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US;q=0.5,en;q=0.3",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-GPC": "1",
        "Cache-Control": "max-age=0",
    }

    resp = get("https://www.bing.com/account/general", headers=headers, timeout=5)
    if not resp.ok:
        raise RuntimeError("Response from Bing is not OK.")

    dom = html.fromstring(resp.text)

    map_market_codes: dict[str, str] = {
        "zh-hk": "en-hk",  # not sure why, but at Microslop this is the market code for Hongkong
    }

    for href in eval_xpath(dom, '//div[@id="region-section-content"]//div[@class="regionItem"]/a/@href'):
        cc_tag = parse_qs(urlparse(href).query)["cc"][0]
        if cc_tag == "clear":
            engine_traits.all_locale = cc_tag
            continue

        # add market codes from official languages of the country ..
        for lang_tag in babel.languages.get_official_languages(cc_tag, de_facto=True):
            lang_tag = lang_tag.split("_")[0]  # zh_Hant --> zh
            market_code = f"{lang_tag}-{cc_tag}"  # zh-tw
            market_code = map_market_codes.get(market_code, market_code)

            try:
                sxng_tag = region_tag(babel.Locale.parse("%s_%s" % (lang_tag, cc_tag.upper())))
            except babel.UnknownLocaleError:
                # silently ignore unknown languages
                continue

            conflict = engine_traits.regions.get(sxng_tag)
            if conflict:
                if conflict != market_code:
                    print("CONFLICT: babel %s --> %s, %s" % (sxng_tag, conflict, market_code))
                continue

            engine_traits.regions[sxng_tag] = market_code
