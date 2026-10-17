# SPDX-License-Identifier: AGPL-3.0-or-later
"""Yahoo Search (Web)

As a bot detection measure, Yahoo has put search behind a cookie
named `YBV`, which is cached for 24h before expiring.

"""

import typing as t
from urllib.parse import unquote, urlencode, urljoin

from searx.enginelib import EngineCache
from searx.network import get  # see https://github.com/searxng/searxng/issues/762
from searx.result_types import EngineResults
from searx.utils import eval_xpath_getindex, eval_xpath_list, extract_text, html_to_text

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://search.yahoo.com/",
    "wikidata_id": None,
    "official_api_documentation": "https://developer.yahoo.com/api/",
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

categories = ["general", "web"]
paging = True
time_range_support = True
safesearch = True

time_range_dict = {"day": "d", "week": "w", "month": "m"}
safesearch_dict = {0: "p", 1: "i", 2: "r"}

region2domain = {
    "CO": "co.search.yahoo.com",  # Colombia
    "TH": "th.search.yahoo.com",  # Thailand
    "VE": "ve.search.yahoo.com",  # Venezuela
    "CL": "cl.search.yahoo.com",  # Chile
    "PE": "pe.search.yahoo.com",  # Peru
    "CA": "ca.search.yahoo.com",  # Canada
    "DE": "de.search.yahoo.com",  # Germany
    "FR": "fr.search.yahoo.com",  # France
    "GB": "uk.search.yahoo.com",  # United Kingdom
    "UK": "uk.search.yahoo.com",
    "BR": "br.search.yahoo.com",  # Brazil
    "IN": "in.search.yahoo.com",  # India
    "ES": "espanol.search.yahoo.com",  # Espanol
    "PH": "ph.search.yahoo.com",  # Philippines
    "AR": "ar.search.yahoo.com",  # Argentina
    "MX": "mx.search.yahoo.com",  # Mexico
    "SG": "sg.search.yahoo.com",  # Singapore
    "AU": "au.search.yahoo.com",  # Australia
    "NZ": "nz.search.yahoo.com",  # New Zealand
    "IE": "ie.search.yahoo.com",  # Ireland
    "ZA": "za.search.yahoo.com",  # South Africa
    "US": "search.yahoo.com",
    "IT": "it.search.yahoo.com",  # Italy
    "NL": "nl.search.yahoo.com",  # Netherlands
    "BE": "be.search.yahoo.com",  # Belgium
    "CH": "ch.search.yahoo.com",  # Switzerland
    "AT": "at.search.yahoo.com",  # Austria
    "SE": "se.search.yahoo.com",  # Sweden
    "NO": "no.search.yahoo.com",  # Norway
    "DK": "dk.search.yahoo.com",  # Denmark
    "FI": "fi.search.yahoo.com",  # Finland
    "GR": "gr.search.yahoo.com",  # Greece
    "TR": "tr.search.yahoo.com",  # Turkey
    "MY": "malaysia.search.yahoo.com",  # Malaysia
    "ID": "id.search.yahoo.com",  # Indonesia
    "VN": "vn.search.yahoo.com",  # Vietnam
    "PL": "pl.search.yahoo.com",  # Poland
    "RO": "ro.search.yahoo.com",  # Romania
}

yahoo_languages = {
    "all": "any",
    "ar": "ar",  # Arabic
    "bg": "bg",  # Bulgarian
    "cs": "cs",  # Czech
    "da": "da",  # Danish
    "de": "de",  # German
    "el": "el",  # Greek
    "en": "en",  # English
    "es": "es",  # Spanish
    "et": "et",  # Estonian
    "fi": "fi",  # Finnish
    "fr": "fr",  # French
    "he": "he",  # Hebrew
    "hr": "hr",  # Croatian
    "hu": "hu",  # Hungarian
    "it": "it",  # Italian
    "ja": "ja",  # Japanese
    "ko": "ko",  # Korean
    "lt": "lt",  # Lithuanian
    "lv": "lv",  # Latvian
    "nl": "nl",  # Dutch
    "no": "no",  # Norwegian
    "pl": "pl",  # Polish
    "pt": "pt",  # Portuguese
    "ro": "ro",  # Romanian
    "ru": "ru",  # Russian
    "sk": "sk",  # Slovak
    "sl": "sl",  # Slovenian
    "sv": "sv",  # Swedish
    "th": "th",  # Thai
    "tr": "tr",  # Turkish
    "zh": "zh_chs",
}


CACHE: EngineCache
"""YBV cookie"""

_YBV_HOPS = 4
"""Tracking pixel -> gif -> (optional) geo redirect i.e. au.search.yahoo.com -> 200"""


def setup(engine_settings: dict[str, t.Any]):
    global CACHE  # pylint: disable=global-statement
    CACHE = EngineCache(engine_settings["name"])


def request(query: str, params: "OnlineParams") -> None:
    parts = params["searxng_locale"].split("-")
    lang = yahoo_languages.get(parts[0], "any")

    url_params: dict[str, str | int] = {"p": query}
    if params["time_range"] in time_range_dict:
        url_params["btf"] = time_range_dict[params["time_range"]]
    if params["pageno"] == 1:
        url_params["iscqry"] = ""
    else:
        url_params["b"] = params["pageno"] * 7 + 1
        url_params["pz"] = 7
        url_params["bct"] = 0
        url_params["xargs"] = 0

    params["cookies"]["sB"] = urlencode(
        {
            "v": 1,
            "vm": safesearch_dict[params["safesearch"]],
            "fl": 1,
            "vl": f"lang_{lang}",
            "pn": 10,
            "rw": "new",
            "userset": 1,
        }
    )

    domain = "search.yahoo.com"
    if len(parts) > 1 and parts[-1] in region2domain:
        domain = region2domain[parts[-1]]
    logger.debug("domain selected: %s", domain)
    params["url"] = f"https://{domain}/search?{urlencode(url_params)}"
    if ybv := CACHE.get("YBV"):
        params["cookies"]["YBV"] = ybv


def parse_url(url_string: str) -> str:
    """remove yahoo-specific tracking-url"""

    endings = ["/RS", "/RK"]
    endpositions = []
    start = url_string.find("http", url_string.find("/RU=") + 1)

    for ending in endings:
        endpos = url_string.rfind(ending)
        if endpos > -1:
            endpositions.append(endpos)

    if start == 0 or len(endpositions) == 0:
        return url_string

    end = min(endpositions)
    return unquote(url_string[start:end])


def _yahoo_html(resp: "SXNG_Response") -> "SXNG_Response":
    cookies = dict(resp.search_params["cookies"])
    params = resp.search_params
    for _ in range(_YBV_HOPS):
        if ybv := resp.cookies.get("YBV"):
            cookies["YBV"] = ybv
            if ybv.startswith("v0.2"):
                CACHE.set("YBV", ybv, expire=86400)

        if resp.status_code == 200:
            return resp

        loc = resp.headers.get("location")
        if resp.status_code not in (302, 307) or not loc:
            return resp

        # request ourselves instead of following it
        resp = get(
            urljoin(resp.url, loc),
            cookies=cookies,
            headers=params["headers"],
            allow_redirects=False,
        )
        resp.search_params = params

    return resp


def response(resp: "SXNG_Response") -> EngineResults:
    resp = _yahoo_html(resp)
    results = EngineResults()
    if resp.status_code != 200:
        resp.raise_for_status()
    dom = resp.html()

    for result in eval_xpath_list(dom, '//div[contains(@class,"algo-sr")]'):
        url = eval_xpath_getindex(result, './/div[contains(@class,"compTitle")]//a/@href', 0, default=None)
        if url is None:
            continue
        url = parse_url(url)
        title = extract_text(eval_xpath_getindex(result, ".//h3//a/@aria-label", 0, default=None), allow_none=True)
        if not title:
            title = extract_text(eval_xpath_getindex(result, ".//a/h3", 0, default=None), allow_none=True)
        if not title:
            continue
        content = extract_text(eval_xpath_getindex(result, './/div[contains(@class, "compText")]', 0))
        results.add(
            results.types.MainResult(
                url=url,
                # title sometimes contains HTML tags / see
                # https://github.com/searxng/searxng/issues/3790
                title=html_to_text(title),
                content=html_to_text(content),
            )
        )

    for suggestion in eval_xpath_list(dom, '//div[contains(@class, "AlsoTry")]//table//a'):
        results.add(results.types.LegacyResult(suggestion=extract_text(suggestion)))

    return results
