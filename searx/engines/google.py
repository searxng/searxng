# SPDX-License-Identifier: AGPL-3.0-or-later
"""This is the implementation of the Google WEB engine.  Some of this
implementations (manly the :py:obj:`get_google_info`) are shared by other
engines:

- :ref:`google images engine`
- :ref:`google news engine`
- :ref:`google videos engine`
- :ref:`google scholar engine`
- :ref:`google autocomplete`

This implementation uses two ``User-Agent`` lines to trick Google, we use the Opera 8.65
line first and SAMSUNG-GT-S5230 second. Web, news, and video use the basic from Samsung
layout and Images use the rich layout from Opera. See `Google discussion`_ for more
information on that topic.

.. _Google discussion: https://github.com/searxng/searxng/issues/6359
"""

import typing as t
from urllib.parse import parse_qs, urlencode, urlparse

import babel
import babel.core
import babel.languages
from curl_cffi import CurlOpt
from lxml import html

from searx.enginelib.traits import EngineTraits
from searx.exceptions import SearxEngineAPIException, SearxEngineCaptchaException
from searx.locales import get_official_locales, language_tag, region_tag
from searx.result_types import EngineResults
from searx.utils import (
    eval_xpath_getindex,
    eval_xpath_list,
    extract_text,
)

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://www.google.com",
    "wikidata_id": "Q9366",
    "official_api_documentation": "https://developers.google.com/custom-search/",
    "use_official_api": False,
    "require_api_key": False,
    "results": "XML",
}

# engine dependent config
categories = ["general", "web"]
paging = True
max_page = 50
"""Google supports up to 50 pages of results, see the `Google max_page discussion`_.

.. _Google max_page discussion: https://github.com/searxng/searxng/issues/2982
"""
time_range_support = True
language_support = True
safesearch = True

time_range_dict = {"day": "d", "week": "w", "month": "m", "year": "y"}

# Filter results. 0: None, 1: Moderate, 2: Strict
filter_mapping = {0: "off", 1: "medium", 2: "high"}

opera_useragent = "Mozilla/4.0 (compatible; MSIE 6.0; Symbian OS; SAMSUNG-GT-S5230) Opera 8.65"
samsung_useragent = "SAMSUNG-GT-S5230"

suggestion_xpath = '//table[contains(@class, "HExoMb")]//a[contains(@class, "ZWRArf")]'


def get_google_info(params: "OnlineParams", eng_traits: EngineTraits) -> dict[str, t.Any]:
    """Composing various (language) properties for the google engines (:ref:`google
    API`).

    This function is called by the various google engines (:ref:`google web
    engine`, :ref:`google images engine`, :ref:`google news engine` and
    :ref:`google videos engine`).

    :param dict param: Request parameters of the engine.  At least
        a ``searxng_locale`` key should be in the dictionary.

    :param eng_traits: Engine's traits fetched from google preferences
        (:py:obj:`searx.enginelib.traits.EngineTraits`)

    :rtype: dict
    :returns:
        Py-Dictionary with the key/value pairs:

        language:
            The language code that is used by google (e.g. ``lang_en`` or
            ``lang_zh-TW``)

        country:
            The country code that is used by google (e.g. ``US`` or ``TW``)

        locale:
            A instance of :py:obj:`babel.core.Locale` build from the
            ``searxng_locale`` value.

        params:
            Py-Dictionary with additional request arguments (can be passed to
            :py:func:`urllib.parse.urlencode`).

            - ``hl`` parameter: specifies the interface language of user interface.
            - ``ie`` parameter: sets the character encoding scheme that should
              be used to interpret the query string ('utf8').
            - ``oe`` parameter: sets the character encoding scheme that should
              be used to decode the XML result ('utf8').

        headers:
            Py-Dictionary with additional HTTP headers (can be passed to
            request's headers)

            - ``Accept: '*/*``

    """

    ret_val: dict[str, t.Any] = {
        "language": None,
        "country": None,
        "params": {},
        "headers": {},
        "cookies": {},
        "locale": None,
    }

    sxng_locale = params.get("searxng_locale", "all")
    try:
        locale = babel.Locale.parse(sxng_locale, sep="-")
    except babel.core.UnknownLocaleError:
        locale = None

    eng_lang = eng_traits.get_language(sxng_locale) or "lang_en"
    lang_code = eng_lang.split("_")[-1]  # lang_zh-TW --> zh-TW / lang_en --> en
    country = eng_traits.get_region(sxng_locale, eng_traits.all_locale)

    # Test zh_hans & zh_hant --> in the topmost links in the result list of list
    # TW and HK you should a find wiktionary.org zh_hant link.  In the result
    # list of zh-CN should not be no hant link instead you should find
    # zh.m.wikipedia.org/zh somewhere in the top.

    # '!go 日 :zh-TW' --> https://zh.m.wiktionary.org/zh-hant/%E6%97%A5
    # '!go 日 :zh-CN' --> https://zh.m.wikipedia.org/zh/%E6%97%A5

    ret_val["language"] = eng_lang
    ret_val["country"] = country
    ret_val["locale"] = locale

    # hl parameter:
    #   The hl parameter specifies the interface language (host language) of
    #   your user interface. To improve the performance and the quality of your
    #   search results, you are strongly encouraged to set this parameter
    #   explicitly.
    #   https://developers.google.com/custom-search/docs/xml_results#hlsp
    # The Interface Language:
    #   https://developers.google.com/custom-search/docs/xml_results_appendices#interfaceLanguages

    # https://github.com/searxng/searxng/issues/2515#issuecomment-1607150817
    ret_val["params"]["hl"] = f"{lang_code}"

    # lr parameter:
    #   The lr (language restrict) parameter restricts search results to
    #   documents written in a particular language.
    #   https://developers.google.com/custom-search/docs/xml_results#lrsp
    #   Language Collection Values:
    #   https://developers.google.com/custom-search/docs/xml_results_appendices#languageCollections
    #
    # To select 'all' languages an empty 'lr' value is used.
    #
    # Different to other google services, Google Scholar supports to select more
    # than one language. The languages are separated by a pipe '|' (logical OR).
    # By example: &lr=lang_zh-TW%7Clang_de selects articles written in
    # traditional chinese OR german language.

    ret_val["params"]["lr"] = eng_lang
    if sxng_locale == "all":
        ret_val["params"]["lr"] = ""

    # cr parameter:
    #   The cr parameter restricts search results to documents originating in a
    #   particular country.
    #   https://developers.google.com/custom-search/docs/xml_results#crsp

    # specify a region (country) only if a region is given in the selected
    # locale --> https://github.com/searxng/searxng/issues/2672

    if country is not None:
        ret_val["params"]["cr"] = ""
        if len(sxng_locale.split("-")) > 1:
            ret_val["params"]["cr"] = "country" + country

    # gl parameter: (mandatory by Google News)
    #   The gl parameter value is a two-letter country code. For WebSearch
    #   results, the gl parameter boosts search results whose country of origin
    #   matches the parameter value. See the Country Codes section for a list of
    #   valid values.
    #   Specifying a gl parameter value in WebSearch requests should improve the
    #   relevance of results. This is particularly true for international
    #   customers and, even more specifically, for customers in English-speaking
    #   countries other than the United States.
    #   https://developers.google.com/custom-search/docs/xml_results#glsp

    # https://github.com/searxng/searxng/issues/2515#issuecomment-1606294635
    # ret_val['params']['gl'] = country

    # ie parameter:
    #   The ie parameter sets the character encoding scheme that should be used
    #   to interpret the query string. The default ie value is latin1.
    #   https://developers.google.com/custom-search/docs/xml_results#iesp

    ret_val["params"]["ie"] = "utf8"

    # oe parameter:
    #   The oe parameter sets the character encoding scheme that should be used
    #   to decode the XML result. The default oe value is latin1.
    #   https://developers.google.com/custom-search/docs/xml_results#oesp

    ret_val["params"]["oe"] = "utf8"

    # num parameter:
    #   The num parameter identifies the number of search results to return.
    #   The default num value is 10, and the maximum value is 20. If you request
    #   more than 20 results, only 20 results will be returned.
    #   https://developers.google.com/custom-search/docs/xml_results#numsp

    # HINT: seems to have no effect (tested in google WEB & Images)
    # ret_val['params']['num'] = 20

    # HTTP headers

    ret_val["headers"]["Accept"] = "*/*"

    # Cookies

    # - https://github.com/searxng/searxng/pull/1679#issuecomment-1235432746
    # - https://github.com/searxng/searxng/issues/1555
    ret_val["cookies"]["CONSENT"] = "YES+"

    return ret_val


def detect_google_sorry(resp: "SXNG_Response"):
    sorry = resp.url.host == "sorry.google.com" or resp.url.path.startswith("/sorry") or resp.status_code == 302
    if sorry or (len(resp.text) < 2000 and "/sorry/" in resp.text):
        raise SearxEngineCaptchaException()


def unwrap_google_url(raw_url: str) -> str:
    target = parse_qs(urlparse(raw_url).query).get("q", [""])[0]
    if target.startswith("CAES"):
        raise SearxEngineAPIException("returned goto links")
    return target if target.startswith("http") else raw_url


def response_dom(resp: "SXNG_Response"):
    detect_google_sorry(resp)
    text = resp.text
    if text.lstrip().startswith("<?xml"):
        text = text.split("?>", 1)[-1]
    return html.fromstring(text)


def google_request(  # pylint: disable=too-many-arguments
    query: str,
    params: "OnlineParams",
    extra_args: dict[str, t.Any] | None = None,
    *,
    eng_traits: EngineTraits | None = None,
    use_time_range: bool = True,
    use_safesearch: bool = True,
    safesearch_map: dict[int, str] | None = None,
    use_locales: bool = True,
    images: bool = False,
) -> None:
    google_info = get_google_info(params, eng_traits or traits)
    if not use_locales:
        google_info["params"].pop("lr", None)
        google_info["params"].pop("cr", None)

    page = params["pageno"] - 1
    args: dict[str, t.Any] = {
        "q": query,
        "sca_esv": "1",
        **google_info["params"],
        **(extra_args or {}),
    }
    if images:
        if page:
            args["ijn"] = page
    elif page:
        args["start"] = page * 10
    if use_time_range and params["time_range"] in time_range_dict:
        args["tbs"] = "qdr:" + time_range_dict[params["time_range"]]
    if use_safesearch and params["safesearch"]:
        args["safe"] = (safesearch_map or filter_mapping)[params["safesearch"]]

    params["url"] = f"https://www.google.com/search?{urlencode(args)}"
    params["default_headers"] = False
    params["impersonate"] = "none"
    params["headers"].pop("Accept-Language", None)
    # A dict would join these into one header. Order is Opera, then Samsung.
    params["headers"] = [  # type: ignore[assignment]
        ("User-Agent", opera_useragent),
        ("User-Agent", samsung_useragent),
    ]
    params["curl_options"] = {CurlOpt.FORBID_REUSE: 1}


def request(query: str, params: "OnlineParams") -> None:
    google_request(query, params)


def response(resp: "SXNG_Response") -> EngineResults:
    results = EngineResults()
    dom = response_dom(resp)

    # parse results
    for card in eval_xpath_list(dom, '//div[contains(@class, "zMzFAb") and .//a[contains(@class, "fuLhoc")]]'):
        url = unwrap_google_url(eval_xpath_getindex(card, './/a[contains(@class, "fuLhoc")]/@href', 0))
        title = extract_text(eval_xpath_getindex(card, './/span[contains(@class, "CVA68e")]', 0, default=""))
        if not title:
            continue
        content = extract_text(
            eval_xpath_getindex(
                card,
                './/span[contains(@class, "FrIlee")]/span[contains(@class, "fYyStc")'
                ' and not(contains(@class, "YVIcad"))]',
                0,
                default="",
            )
        )
        results.add(results.types.MainResult(url=url, title=title, content=content))

    # parse suggestion
    for suggestion in eval_xpath_list(dom, suggestion_xpath):
        results.add(results.types.LegacyResult(suggestion=extract_text(suggestion)))

    return results


# get supported languages from their site


skip_countries = [
    # official language of google-country not in google-languages
    "AL",  # Albanien (sq)
    "AZ",  # Aserbaidschan  (az)
    "BD",  # Bangladesch (bn)
    "BN",  # Brunei Darussalam (ms)
    "BT",  # Bhutan (dz)
    "ET",  # Äthiopien (am)
    "GE",  # Georgien (ka, os)
    "GL",  # Grönland (kl)
    "KH",  # Kambodscha (km)
    "LA",  # Laos (lo)
    "LK",  # Sri Lanka (si, ta)
    "ME",  # Montenegro (sr)
    "MK",  # Nordmazedonien (mk, sq)
    "MM",  # Myanmar (my)
    "MN",  # Mongolei (mn)
    "MV",  # Malediven (dv) // dv_MV is unknown by babel
    "MY",  # Malaysia (ms)
    "NP",  # Nepal (ne)
    "TJ",  # Tadschikistan (tg)
    "TM",  # Turkmenistan (tk)
    "UZ",  # Usbekistan (uz)
]


def fetch_traits(engine_traits: EngineTraits):
    """Fetch languages from Google."""
    # pylint: disable=import-outside-toplevel, too-many-branches

    from searx.network import get  # see https://github.com/searxng/searxng/issues/762

    resp = get("https://www.google.com/preferences", timeout=5)
    if not resp.ok:
        raise RuntimeError("Response from Google preferences is not OK.")

    dom = html.fromstring(resp.text.replace('<?xml version="1.0" encoding="UTF-8"?>', ""))

    # supported language codes

    lang_map = {"no": "nb"}
    for x in eval_xpath_list(dom, "//select[@name='hl']/option"):
        eng_lang = x.get("value")
        try:
            locale = babel.Locale.parse(lang_map.get(eng_lang, eng_lang), sep="-")
        except babel.UnknownLocaleError:
            print("INFO:  google UI language %s (%s) is unknown by babel" % (eng_lang, x.text.split("(")[0].strip()))
            continue
        sxng_lang = language_tag(locale)

        conflict = engine_traits.languages.get(sxng_lang)
        if conflict:
            if conflict != eng_lang:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_lang, conflict, eng_lang))
            continue
        engine_traits.languages[sxng_lang] = "lang_" + eng_lang

    # alias languages
    engine_traits.languages["zh"] = "lang_zh-CN"

    # supported region codes

    for x in eval_xpath_list(dom, "//select[@name='gl']/option"):
        eng_country = x.get("value")

        if eng_country in skip_countries:
            continue
        if eng_country == "ZZ":
            engine_traits.all_locale = "ZZ"
            continue

        sxng_locales = get_official_locales(eng_country, engine_traits.languages.keys(), regional=True)

        if not sxng_locales:
            print("ERROR: can't map from google country %s (%s) to a babel region." % (x.get("data-name"), eng_country))
            continue

        for sxng_locale in sxng_locales:
            engine_traits.regions[region_tag(sxng_locale)] = eng_country

    # alias regions
    engine_traits.regions["zh-CN"] = "HK"
