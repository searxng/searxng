# SPDX-License-Identifier: AGPL-3.0-or-later
"""This engine uses the Qwant API (https://api.qwant.com/v3) to implement Qwant
-Web, -News, -Images and -Videos.  The API is undocumented but can be reverse
engineered by reading the network log of https://www.qwant.com/ queries.

For Qwant's *web-search* two alternatives are implemented:

- ``web``: uses the :py:obj:`api_url` which returns a JSON structure


Configuration
=============

The engine has the following additional settings:

- :py:obj:`qwant_categ`

This implementation is used by different qwant engines in the :ref:`settings.yml
<settings engines>`:

.. code:: yaml

  - name: qwant
    qwant_categ: web
    ...
  - name: qwant news
    qwant_categ: news
    ...
  - name: qwant images
    qwant_categ: images
    ...
  - name: qwant videos
    qwant_categ: videos
    ...

Implementations
===============

"""

import random
import typing as t

from datetime import (
    datetime,
    timedelta,
)
from json import loads
from urllib.parse import urlencode

import babel
from flask_babel import gettext  # pyright: ignore[reportUnknownVariableType]

from searx.enginelib import EngineCache
from searx.enginelib.traits import EngineTraits
from searx.exceptions import (
    SearxEngineAccessDeniedException,
    SearxEngineAPIException,
    SearxEngineCaptchaException,
    SearxEngineTooManyRequestsException,
)
from searx.network import raise_for_httperror
from searx.utils import (
    get_embeded_stream_url,
)
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.search.processors import OnlineParams
    from searx.extended_types import SXNG_Response

# about
about = {
    "website": "https://www.qwant.com/",
    "wikidata_id": "Q14657870",
    "official_api_documentation": None,
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

# engine dependent config
categories = []
paging = True
max_page = 5
"""5 pages maximum (``&p=5``): Trying to do more just results in an improper
redirect"""

qwant_categ: str = None  # pyright: ignore[reportAssignmentType]
"""One of ``web``, ``news``, ``images`` or ``videos``"""

safesearch = True

# tgp seems to be short for "test group" - its actual value doesn't matter, as
# long as it's sent and at the correct position in the query params and doesn't
# change too frequently
test_group_value = random.randint(1, 3)

# fmt: off
qwant_news_locales = [
    "ca_ad", "ca_es", "ca_fr", "co_fr", "de_at", "de_ch", "de_de", "en_au",
    "en_ca", "en_gb", "en_ie", "en_my", "en_nz", "en_us", "es_ad", "es_ar",
    "es_cl", "es_co", "es_es", "es_mx", "es_pe", "eu_es", "eu_fr", "fc_ca",
    "fr_ad", "fr_be", "fr_ca", "fr_ch", "fr_fr", "it_ch", "it_it", "nl_be",
    "nl_nl", "pt_ad", "pt_pt",
]
# fmt: on

base_url = "https://www.qwant.com"
api_url = "https://api.qwant.com/v3/search/"
"""URL of Qwant's API (JSON)"""

CACHE: EngineCache
"""Cache for storing the ``datadome`` cookie."""


def setup(engine_settings: dict[str, t.Any]) -> bool:
    global CACHE  # pylint: disable=global-statement
    CACHE = EngineCache(engine_settings["name"])
    return True


def request(query: str, params: "OnlineParams") -> None:
    """Qwant search request"""

    if not query:
        return

    q_locale = traits.get_region(params["searxng_locale"], default="en_US")

    results_per_page = 10
    if qwant_categ == "images":
        results_per_page = 50

    args = {
        "q": query,
        "count": results_per_page,
        "locale": q_locale,
        "offset": (params["pageno"] - 1) * results_per_page,
        "tgp": test_group_value,
        "device": "desktop",
        "safesearch": params["safesearch"],
        # True would be encoded to "True", instead of "true", which makes the request
        # easier to detect and block
        "displayed": "true",
        "llm": "true",
    }

    params["raise_for_httperror"] = False

    params["url"] = f"{api_url}{qwant_categ}?{urlencode(args)}"

    params["cookies"]["datadome"] = CACHE.get("datadome")
    params["headers"].update({"Accept": "application/json", "Referer": f"{base_url}/", "Origin": base_url})


def response(resp: "SXNG_Response") -> EngineResults:
    """Parse results from Qwant's API"""
    # pylint: disable=too-many-locals, too-many-branches, too-many-statements

    # cache datadome cookie - changes on each request
    datadome = resp.cookies.get("datadome")
    if datadome:
        CACHE.set("datadome", datadome)

    res = EngineResults()

    # Try to load JSON result
    search_results: dict[str, t.Any] = {}
    try:
        search_results = resp.json()
    except ValueError:
        pass

    data: dict[str, t.Any] = search_results.get("data", {})  # pyright: ignore[reportAny]

    # check for an API error
    if search_results.get("status") != "success":
        error_code = data.get("error_code")
        if error_code == 24:
            raise SearxEngineTooManyRequestsException()
        if search_results.get("url") is not None:
            raise SearxEngineCaptchaException(suspended_time=0)
        if resp.status_code == 403:
            raise SearxEngineAccessDeniedException()
        msg = ",".join(data.get("message", ["unknown"]))
        raise SearxEngineAPIException(f"{msg} ({error_code})")

    # raise for other errors
    raise_for_httperror(resp)

    if qwant_categ == "web":
        # The WEB query contains a list named 'mainline'.  This list can contain
        # different result types (e.g. mainline[0]["type"] returns type of the
        # result items in mainline[0]["items"]
        mainline = data.get("result", {}).get("items", {}).get("mainline", {})
    else:
        # Queries on News, Images and Videos do not have a list named 'mainline'
        # in the response.  The result items are directly in the list
        # result["items"].
        mainline = data.get("result", {}).get("items", [])
        mainline = [
            {"type": qwant_categ, "items": mainline},
        ]

    # return empty array if there are no results
    if not mainline:
        return res

    row: dict[str, t.Any]
    for row in mainline:
        mainline_type = row.get("type", "web")
        if mainline_type != qwant_categ:
            continue

        if mainline_type == "ads":
            # ignore adds
            continue

        mainline_items: list[dict[str, t.Any]] = row.get("items", [])
        for item in mainline_items:
            title: str = item.get("title", "")
            res_url: str = item.get("url", "")
            pub_date: datetime | None = None
            thumbnail: str = ""
            content: str = item.get("desc", "")

            _date: float | None = item.get("date")
            if _date:
                try:
                    pub_date = datetime.fromtimestamp(_date)
                except ValueError:
                    # news' date value milli seconds
                    pub_date = datetime.fromtimestamp(_date / 1000)

            if mainline_type == "web":
                res.add(
                    res.types.MainResult(
                        title=title,
                        url=res_url,
                        content=content,
                    )
                )

            elif mainline_type == "news":
                news_media = item.get("media", [])
                if news_media:
                    thumbnail = news_media[0].get("pict", {}).get("url", "")

                res.add(
                    res.types.MainResult(
                        title=title,
                        content=content,
                        url=res_url,
                        publishedDate=pub_date,
                        thumbnail=thumbnail,
                    )
                )

            elif mainline_type == "images":
                res.add(
                    res.types.LegacyResult(
                        title=title,
                        url=res_url,
                        template="images.html",
                        thumbnail_src=item["thumbnail"] or "",
                        img_src=item["media"] or "",
                        resolution=f"{item['width']} x {item['height']}",
                        img_format=item.get("thumb_type"),
                    )
                )

            elif mainline_type == "videos":
                # some videos do not have a description: while qwant-video
                # returns an empty string, such video from a qwant-web query
                # miss the 'desc' key.

                d: str = item.get("desc", "")
                s: str = item.get("source", "")
                c: str = item.get("channel", "")

                content_parts: list[str] = []
                if d:
                    content_parts.append(f"{d}")
                if s:
                    content_parts.append(f"{gettext('Source')}: {s} ")
                if c:
                    content_parts.append(f"{gettext('Channel')}: {c} ")
                content = " // ".join(content_parts)

                length = timedelta(milliseconds=(item["duration"] or 0))
                thumbnail = item["thumbnail"] or ""
                # from some locations (DE and others?) the s2 link do
                # response a 'Please wait ..' but does not deliver the thumbnail
                thumbnail = thumbnail.replace("https://s2.qwant.com", "https://s1.qwant.com", 1)

                res.add(
                    res.types.LegacyResult(
                        title=title,
                        url=res_url,
                        content=content,
                        iframe_src=get_embeded_stream_url(res_url),
                        publishedDate=pub_date,
                        thumbnail=thumbnail,
                        template="videos.html",
                        length=length,
                    )
                )

    return res


def fetch_traits(engine_traits: EngineTraits):

    # pylint: disable=import-outside-toplevel
    from searx.locales import region_tag
    from searx.network import get  # see https://github.com/searxng/searxng/issues/762
    from searx.utils import extr

    resp = get(
        base_url,  # pyright: ignore[reportArgumentType]
        timeout=5,
    )
    if not resp.ok:
        raise RuntimeError("Response from Qwant is not OK.")

    json_string = extr(resp.text, "INITIAL_PROPS = ", "</script>")

    q_initial_props = loads(json_string)
    q_locales = q_initial_props.get("locales")
    eng_tag_list: set[str] = set()

    for country, v in q_locales.items():
        for lang in v["langs"]:
            _locale = "{lang}_{country}".format(lang=lang, country=country)

            if qwant_categ == "news" and _locale.lower() not in qwant_news_locales:
                # qwant-news does not support all locales from qwant-web:
                continue

            eng_tag_list.add(_locale)

    for eng_tag in eng_tag_list:
        try:
            sxng_tag = region_tag(babel.Locale.parse(eng_tag, sep="_"))
        except babel.UnknownLocaleError:
            print("ERROR: can't determine babel locale of quant's locale %s" % eng_tag)
            continue

        conflict = engine_traits.regions.get(sxng_tag)
        if conflict:
            if conflict != eng_tag:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_tag, conflict, eng_tag))
            continue
        engine_traits.regions[sxng_tag] = eng_tag
