# SPDX-License-Identifier: AGPL-3.0-or-later
"""This is the implementation of the Google News engine.

Google News has a different region handling compared to Google WEB.

- the ``ceid`` argument has to be set (:py:obj:`ceid_list`)
- the hl_ argument has to be set correctly (and different to Google WEB)
- the gl_ argument is mandatory

If one of this argument is not set correctly, the request is redirected to
CONSENT dialog::

  https://consent.google.com/m?continue=

The google news API ignores some parameters from the common :ref:`google API`:

- num_ : the number of search results is ignored / there is no paging all
  results for a query term are in the first response.
- save_ : is ignored / Google-News results are always *SafeSearch*

.. _hl: https://developers.google.com/custom-search/docs/xml_results#hlsp
.. _gl: https://developers.google.com/custom-search/docs/xml_results#glsp
.. _num: https://developers.google.com/custom-search/docs/xml_results#numsp
.. _save: https://developers.google.com/custom-search/docs/xml_results#safesp
"""
import typing as t

import json
import base64
from urllib.parse import urlencode
from lxml import html
import babel

from searx import locales
from searx.utils import (
    eval_xpath,
    eval_xpath_list,
    eval_xpath_getindex,
    extract_text,
)

from searx.engines.google import fetch_traits as _fetch_traits  # pylint: disable=unused-import
from searx.engines.google import (
    get_google_info,
    detect_google_sorry,
)
from searx.enginelib.traits import EngineTraits

from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

# about
about = {
    "website": "https://news.google.com",
    "wikidata_id": "Q12020",
    "official_api_documentation": "https://developers.google.com/custom-search",
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

# engine dependent config
categories = ["news"]
paging = False
time_range_support = False

# Google-News results are always *SafeSearch*. Option 'safesearch' is set to
# False here.
#
#  safesearch : results are identical for safesearch=0 and safesearch=2
safesearch = True
base_url: str = "https://news.google.com"


def request(query: str, params: "OnlineParams") -> None:
    """Google-News search request"""

    sxng_locale = params.get("searxng_locale", "en-US")
    ceid: str = locales.get_engine_locale(
        sxng_locale, traits.custom["ceid"], default="US:en"
    )  # pyright: ignore[reportAssignmentType]
    google_info = get_google_info(params, traits)
    google_info["subdomain"] = "news.google.com"  # google news has only one domain

    ceid_region, ceid_lang = ceid.split(":")
    ceid_lang, ceid_suffix = (
        ceid_lang.split(":")
        + [
            "",
        ]
    )[:2]

    google_info["params"]["hl"] = ceid_lang

    if ceid_suffix and ceid_suffix not in ["Hans", "Hant"]:

        if ceid_region.lower() == ceid_lang:
            google_info["params"]["hl"] = ceid_lang + "-" + ceid_region
        else:
            google_info["params"]["hl"] = ceid_lang + "-" + ceid_suffix

    elif ceid_region.lower() != ceid_lang:

        if ceid_region in ["AT", "BE", "CH", "IL", "SA", "IN", "BD", "PT"]:
            google_info["params"]["hl"] = ceid_lang
        else:
            google_info["params"]["hl"] = ceid_lang + "-" + ceid_region

    google_info["params"]["lr"] = "lang_" + ceid_lang.split("-")[0]
    google_info["params"]["gl"] = ceid_region

    query_url = (
        "https://"
        + google_info["subdomain"]
        + "/search?"
        + urlencode(
            {"q": query, **google_info["params"]},
        )
        # ceid includes a ':' character which must not be urlencoded
        + ("&ceid=%s" % ceid)
    )

    params["url"] = query_url
    params["cookies"] = google_info["cookies"]
    params["headers"].update(google_info["headers"])


def response(resp: "SXNG_Response") -> EngineResults:
    """Get response from google's search request"""

    res = EngineResults()

    detect_google_sorry(resp)

    # convert the text to dom
    dom = html.fromstring(resp.text)

    for result in eval_xpath_list(dom, "//div[@jslog and @data-n-tid and @jsdata]"):

        url: str = eval_xpath_getindex(result, "./a[@target='_blank']/@href", 0, default=0)
        if not url:
            continue
        if url.startswith("./"):
            url = base_url + url[1:]

        # The real URL is often encoded in the "jslog" attribute
        jslog: str | None = eval_xpath_getindex(result, "./a[@target='_blank']/@jslog", 0, default=None)

        # Try to extract the real URL from jslog
        real_url: str | None = None
        if jslog:
            # jslog format is usually: "95014; 5:<base64>; track:click,vis".  We
            # want the second part (index 1) after splitting by ";"
            parts: list[str] = jslog.split(";")
            if len(parts) > 1:
                b64_data: str = parts[1].split(":")[-1].strip()
                # Pad base64 if necessary
                b64_data += "=" * (-len(b64_data) % 4)
                decoded_data: list[str | None] = json.loads(base64.b64decode(b64_data).decode("utf-8"))
                # The URL is typically the last element in the decoded array
                if (
                    isinstance(decoded_data, list)
                    and isinstance(decoded_data[-1], str)
                    and decoded_data[-1].startswith("http")
                ):
                    real_url = decoded_data[-1]
        if real_url:
            url = real_url
        else:
            logger.error(f"no real-url found: {url}")
            continue

        title = extract_text(eval_xpath(result, "./h4")) or ""

        # The pub_date is mostly a string like 'yesterday', not a real timezone
        # date or time.  Therefore we can't use publishedDate and place the
        # *pub* sting into the content.

        pub_date = extract_text(eval_xpath(result, ".//time"))
        pub_origin = extract_text(eval_xpath(result, ".//div[contains(@class, 'vr1PYe')]"))
        content = " / ".join([x for x in [pub_origin, pub_date] if x])

        thumbnail: str = eval_xpath_getindex(result, ".//figure/img/@src", 0, default="")
        if thumbnail and thumbnail.startswith("/"):
            thumbnail = base_url + thumbnail

        res.add(
            res.types.MainResult(
                url=url,
                title=title,
                content=content,
                thumbnail=thumbnail,
            )
        )

    return res


ceid_list = [
    "AE:ar",
    "AR:es-419",
    "AT:de",
    "AU:en",
    "BD:bn",
    "BE:fr",
    "BE:nl",
    "BG:bg",
    "BR:pt-419",
    "BW:en",
    "CA:en",
    "CA:fr",
    "CH:de",
    "CH:fr",
    "CL:es-419",
    "CN:zh-Hans",
    "CO:es-419",
    "CU:es-419",
    "CZ:cs",
    "DE:de",
    "EE:et",
    "EG:ar",
    "ES:ca",
    "ES:es",
    "ET:en",
    "FI:fi",
    "FR:fr",
    "GB:en",
    "GH:en",
    "GR:el",
    "HK:zh-Hant",
    "HU:hu",
    "ID:en",
    "ID:id",
    "IE:en",
    "IL:en",
    "IL:he",
    "IN:bn",
    "IN:en",
    "IN:gu",
    "IN:hi",
    "IN:ml",
    "IN:mr",
    "IN:pa",
    "IN:ta",
    "IN:te",
    "IT:it",
    "JP:ja",
    "KE:en",
    "KR:ko",
    "LB:ar",
    "LT:lt",
    "LV:en",
    "LV:lv",
    "MA:fr",
    "MY:en",
    "MY:ms",
    "NA:en",
    "NG:en",
    "NL:nl",
    "NO:no",
    "NZ:en",
    "PH:en",
    "PK:en",
    "PL:pl",
    "RO:ro",
    "RS:sr",
    "RU:ru",
    "SA:ar",
    "SE:sv",
    "SG:en",
    "SI:sl",
    "SK:sk",
    "SN:fr",
    "TH:th",
    "TR:tr",
    "TZ:en",
    "UA:ru",
    "UA:uk",
    "UG:en",
    "US:en",
    "VN:vi",
    "ZA:en",
    "ZW:en",
]
"""List of region/language combinations supported by Google News.  Values of the
``ceid`` argument of the Google News REST API."""


_skip_values = [
    "ET:en",  # english (ethiopia)
    "ID:en",  # english (indonesia)
    "LV:en",  # english (latvia)
]

_ceid_locale_map = {"NO:no": "nb-NO"}


def fetch_traits(engine_traits: EngineTraits):
    _fetch_traits(engine_traits, add_domains=False)

    engine_traits.custom["ceid"] = {}

    for ceid in ceid_list:
        if ceid in _skip_values:
            continue

        region, lang = ceid.split(":")
        x = lang.split("-")
        if len(x) > 1:
            if x[1] not in ["Hant", "Hans"]:
                lang = x[0]

        sxng_locale = _ceid_locale_map.get(ceid, lang + "-" + region)
        try:
            locale = babel.Locale.parse(sxng_locale, sep="-")
        except babel.UnknownLocaleError:
            print("ERROR: %s -> %s is unknown by babel" % (ceid, sxng_locale))
            continue

        engine_traits.custom["ceid"][locales.region_tag(locale)] = ceid
