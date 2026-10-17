# SPDX-License-Identifier: AGPL-3.0-or-later
"""Brave supports the categories listed in :py:obj:`brave_category` (General,
news, videos, images).  The support of :py:obj:`paging` and :py:obj:`time range
<time_range_support>` is limited (see remarks).

Configured ``brave`` engines:

.. code:: yaml

  - name: brave
    engine: brave
    ...
    brave_category: search
    time_range_support: true
    paging: true

  - name: brave.images
    engine: brave
    ...
    brave_category: images

  - name: brave.videos
    engine: brave
    ...
    brave_category: videos

  - name: brave.news
    engine: brave
    ...
    brave_category: news

  - name: brave.goggles
    time_range_support: true
    paging: true
    ...
    brave_category: goggles


.. _brave regions:

Brave regions
=============

Brave uses two-digit tags for the regions like ``ca`` while SearXNG deals with
locales.  To get a mapping, all *officiat de-facto* languages of the Brave
region are mapped to regions in SearXNG (see :py:obj:`babel
<babel.languages.get_official_languages>`):

.. code:: python

    "regions": {
      ..
      "en-CA": "ca",
      "fr-CA": "ca",
      ..
     }


.. note::

   The language (aka region) support of Brave's index is limited to very basic
   languages.  The search results for languages like Chinese or Arabic are of
   low quality.


.. _brave googles:

Brave Goggles
=============

.. _list of Goggles: https://search.brave.com/goggles/discover
.. _Goggles Whitepaper: https://brave.com/static-assets/files/goggles.pdf
.. _Goggles Quickstart: https://github.com/brave/goggles-quickstart

Goggles allow you to choose, alter, or extend the ranking of Brave Search
results (`Goggles Whitepaper`_).  Goggles are openly developed by the community
of Brave Search users.

Select from the `list of Goggles`_ people have published, or create your own
(`Goggles Quickstart`_).


.. _brave languages:

Brave languages
===============

Brave's language support is limited to the UI (menus, area local notations,
etc).  Brave's index only seems to support a locale, but it does not seem to
support any languages in its index.  The choice of available languages is very
small (and its not clear to me where the difference in UI is when switching
from en-us to en-ca or en-gb).

In the :py:obj:`EngineTraits object <searx.enginelib.traits.EngineTraits>` the
UI languages are stored in a custom field named ``ui_lang``:

.. code:: python

    "custom": {
      "ui_lang": {
        "ca": "ca",
        "de-DE": "de-de",
        "en-CA": "en-ca",
        "en-GB": "en-gb",
        "en-US": "en-us",
        "es": "es",
        "fr-CA": "fr-ca",
        "fr-FR": "fr-fr",
        "ja-JP": "ja-jp",
        "pt-BR": "pt-br",
        "sq-AL": "sq-al"
      }
    },

Implementations
===============

"""

import json
import typing as t
from collections.abc import Callable
from urllib.parse import urlencode

from dateutil import parser

from searx import locales, logger
from searx.enginelib.traits import EngineTraits
from searx.exceptions import SearxEngineResponseException
from searx.result_types import EngineResults, MainResult, Video
from searx.result_types.image import Image
from searx.utils import html_to_text, js_obj_str_to_json_str, js_obj_str_to_python

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response

about = {
    "website": "https://search.brave.com/",
    "wikidata_id": "Q22906900",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

base_url = "https://search.brave.com/"
categories = []
enable_http3 = True
brave_category: t.Literal["search", "videos", "images", "news", "goggles"] = "search"
"""Brave supports common web-search, videos, images, news, and goggles search.

- ``search``: Common WEB search
- ``videos``: search for videos
- ``images``: search for images
- ``news``: search for news
- ``goggles``: Common WEB search with custom rules, requires a :py:obj:`Goggles` URL.
"""

Goggles: str = ""
"""This should be a URL ending in ``.goggle``"""

brave_spellcheck = False
"""Brave supports some kind of spell checking.  When activated, Brave tries to
fix typos, e.g. it searches for ``food`` when the user queries for ``fooh``.  In
the UI of Brave the user gets warned about this, since we can not warn the user
in SearXNG, the spellchecking is disabled by default.
"""

paging = False
"""Brave only supports paging in :py:obj:`brave_category` ``search`` (UI
category All) and in the goggles category."""
max_page = 10
"""Tested 9 pages maximum (``&offset=8``), to be save max is set to 10.  Trying
to do more won't return any result and you will most likely be flagged as a bot.
"""

safesearch = True
safesearch_map = {2: "strict", 1: "moderate", 0: "off"}  # cookie: safesearch=off

time_range_support = False
"""Brave only supports time-range in :py:obj:`brave_category` ``search`` (UI
category All) and in the goggles category."""

time_range_map: dict[str, str] = {
    "day": "pd",
    "week": "pw",
    "month": "pm",
    "year": "py",
}


def request(query: str, params: dict[str, t.Any]) -> None:

    args: dict[str, t.Any] = {
        "q": query,
        "source": "web",
    }
    if brave_spellcheck:
        args["spellcheck"] = "1"

    if brave_category in ("search", "goggles"):
        if params.get("pageno", 1) - 1:
            args["offset"] = params.get("pageno", 1) - 1
        if time_range_map.get(params["time_range"]):
            args["tf"] = time_range_map.get(params["time_range"])

    if brave_category == "goggles":
        args["goggles_id"] = Goggles

    params["headers"]["Accept-Encoding"] = "gzip, deflate"
    params["url"] = f"{base_url}{brave_category}?{urlencode(args)}"
    logger.debug("url %s", params["url"])

    # set properties in the cookies

    params["cookies"]["safesearch"] = safesearch_map.get(params["safesearch"], "off")
    # the useLocation is IP based, we use cookie "country" for the region
    params["cookies"]["useLocation"] = "0"
    params["cookies"]["summarizer"] = "0"

    engine_region = traits.get_region(params["searxng_locale"], "all")
    params["cookies"]["country"] = engine_region.split("-")[-1].lower()  # type: ignore

    ui_lang = locales.get_engine_locale(params["searxng_locale"], traits.custom["ui_lang"], "en-us")
    params["cookies"]["ui_lang"] = ui_lang
    logger.debug("cookies %s", params["cookies"])


def _extract_published_date(published_date_raw: str | None):
    if published_date_raw is None:
        return None
    try:
        return parser.parse(published_date_raw)
    except parser.ParserError:
        return None


def extract_json_data(text: str) -> dict[str, t.Any]:
    # Example script source containing the data:
    #
    # kit.start(app, element, {
    #    node_ids: [0, 19],
    #    data: [{type:"data",data: .... ["q","goggles_id"],route:1,url:1}}]
    #          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #    form: null,
    #    error: null
    # });
    start = text.index("data: [{")
    newline = text.index("\n", start)
    end = text.rindex("}}]", start, newline)
    js_obj_str = "{" + text[start:end] + "}}]}"
    # js_obj_str = js_obj_str.replace("\xa0", "")  # remove ASCII for &nbsp;
    # js_obj_str = js_obj_str.replace(r"\u003C", "<").replace(r"\u003c", "<")  # fix broken HTML tags in strings
    json_str = js_obj_str_to_json_str(js_obj_str)
    data: dict[str, t.Any] = json.loads(json_str)
    return data


def response(resp: "SXNG_Response") -> EngineResults:
    # delegate the response to the appropriate parser based on search type

    match brave_category:
        case "search" | "goggles":
            return _parse_results(parse_search_result, resp)
        case "news":
            return _parse_results(parse_news_result, resp)
        case "images":
            return _parse_results(parse_image_result, resp)
        case "videos":
            return _parse_results(parse_video_result, resp)
        case _:
            raise ValueError(f"Unsupported brave category: {brave_category}")  # pyright: ignore[reportUnreachable]


def parse_search_result(result: dict[str, t.Any]) -> MainResult:
    thumbnail: dict[str, t.Any] = result.get("thumbnail", {})
    return MainResult(
        template="default.html",
        title=result.get("title", ""),
        content=html_to_text(result.get("description", "")),
        url=result.get("url", ""),
        publishedDate=_extract_published_date(result.get("page_age")),
        pubdate=result.get("age", ""),
        thumbnail=thumbnail.get("src", "") if thumbnail and not thumbnail.get("logo") else "",
    )


def _parse_secondary_items(json_data: dict[str, t.Any], results: EngineResults):
    # video results utilize same schema as video search -> re-use _parse_video_result
    body_resp: dict[str, t.Any] = _get_response_data(json_data)
    videos_resp: dict[str, t.Any] = body_resp.get("videos", {})
    if videos_resp and "results" in videos_resp:
        for result in videos_resp.get("results", []):
            results.add(parse_video_result(result))
    # related queries -> suggestion
    query: dict[str, t.Any] = body_resp.get("query", {})
    if query and "related_queries" in query:
        for x in query.get("related_queries", []):
            suggestion = " ".join(val[1] for val in x)
            results.add(results.types.LegacyResult(suggestion=suggestion))


def parse_news_result(result: dict[str, t.Any]) -> MainResult:
    thumbnail: dict[str, t.Any] = result.get("thumbnail", {})
    return MainResult(
        title=result.get("title", ""),
        content=result.get("description", ""),
        url=result.get("url"),
        publishedDate=_extract_published_date(result.get("age")),
        pubdate=result.get("age", ""),
        thumbnail=thumbnail.get("src", "") if thumbnail else "",
    )


def parse_image_result(result: dict[str, t.Any]) -> Image:
    properties: dict[str, t.Any] = result.get("properties", {})
    thumbnail: dict[str, t.Any] = result.get("thumbnail", {})
    width, height = properties.get("width"), properties.get("height")

    return Image(
        title=result.get("title", ""),
        url=result.get("url"),
        img_src=properties.get("url", ""),
        thumbnail_src=thumbnail.get("src", "") if thumbnail else "",
        source=result.get("source", ""),
        resolution=f"{width}x{height}" if width and height else "",
    )


def parse_video_result(result: dict[str, t.Any]) -> Video:
    video: dict[str, t.Any] = result.get("video", {})
    thumbnail: dict[str, t.Any] = result.get("thumbnail", {})

    return Video(
        title=result.get("title", ""),
        url=result.get("url"),
        content=result.get("description", ""),
        length=video.get("duration"),
        publishedDate=_extract_published_date(result.get("age")),
        pubdate=result.get("age", ""),
        views=video.get("views", ""),
        thumbnail=thumbnail.get("src", "") if thumbnail else "",
    )


def _get_response_data(json_data: dict[str, t.Any], category: str | None = None) -> dict[str, t.Any]:
    """Navigate the Brave embedded JSON to the category-specific response object."""
    # Brave’s structure is mostly consistent but has a couple of quirks:
    # - most categories live under data[1].data.body.response.<category>
    # - news omits the intermediate "body" key
    try:
        data: dict[str, t.Any] = json_data["data"][1]["data"]

        if data.get("noResults"):  # Boolean Value
            return {}

        if category == "news":
            return data["response"]["news"]

        body_resp = data["body"]["response"]
        if category in ("search", "goggles"):
            return body_resp["web"]
        # images / videos / secondary items
        return body_resp
    except (KeyError, IndexError, TypeError) as e:
        raise SearxEngineResponseException(f"Unexpected Brave JSON structure for category {category!r}") from e


def _parse_results(parse_func: Callable[..., MainResult | Image], resp: "SXNG_Response") -> EngineResults:
    """Extract json data and loop through result list
    The suppled :py.obj:`parse_func` parses individual result items
    General search / goggle search relies on :py.obj:`_parse_secondary_items` for mixed result-types"""
    # Example script source containing the data:
    #
    # kit.start(app, element, {
    #    node_ids: [0, 19],
    #    data: [{type:"data",data: .... ["q","goggles_id"],route:1,url:1}}]
    #          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    results = EngineResults()
    json_data: dict[str, t.Any] = extract_json_data(resp.text)
    json_resp: dict[str, t.Any] = _get_response_data(json_data, brave_category)
    if not json_resp:
        # if _get_response_data returns {} - indicates it was parsed successfully but had "noResults" = True
        return results

    json_results: list[dict[str, t.Any]] = json_resp["results"]
    for result in json_results:
        results.add(parse_func(result))

    # general search / goggle might have secondary items
    if brave_category in ("search", "goggles"):
        _parse_secondary_items(json_data, results)

    return results


def fetch_traits(engine_traits: EngineTraits):
    """Fetch :ref:`languages <brave languages>` and :ref:`regions <brave
    regions>` from Brave."""

    # pylint: disable=import-outside-toplevel, too-many-branches

    import babel.languages

    from searx.locales import language_tag, region_tag
    from searx.network import get  # see https://github.com/searxng/searxng/issues/762

    engine_traits.custom["ui_lang"] = {}

    lang_map = {"no": "nb"}  # norway

    # languages (UI)

    resp = get("https://search.brave.com/settings", timeout=5)
    if not resp.ok:
        raise RuntimeError("Response from Brave languages is not OK.")

    dom = resp.html()

    for option in dom.xpath("//section//option[@value='en-us']/../option"):
        ui_lang = option.get("value")
        try:
            l = babel.Locale.parse(ui_lang, sep="-")
            if l.territory:
                sxng_tag = region_tag(babel.Locale.parse(ui_lang, sep="-"))
            else:
                sxng_tag = language_tag(babel.Locale.parse(ui_lang, sep="-"))
        except babel.UnknownLocaleError:
            # silently ignore unknown languages
            continue

        if conflict := engine_traits.custom["ui_lang"].get(sxng_tag):
            if conflict != ui_lang:
                print(f"CONFLICT: babel {sxng_tag} --> {conflict}, {ui_lang}")
            continue
        engine_traits.custom["ui_lang"][sxng_tag] = ui_lang

    # search regions of brave

    resp = get(
        "https://cdn.search.brave.com/serp/v2/_app/immutable/chunks/parameters.734c106a.js",
        timeout=5,
    )
    if not resp.ok:
        raise RuntimeError("Response from Brave regions is not OK.")

    country_js = resp.text[resp.text.index("options:{all") + len("options:") :]
    country_js = country_js[: country_js.index("},k={default")]
    country_tags = js_obj_str_to_python(country_js)

    for k, v in country_tags.items():
        if k == "all":
            engine_traits.all_locale = "all"
            continue
        country_tag = v["value"]

        # add official languages of the country ..
        for lang_tag in babel.languages.get_official_languages(country_tag, de_facto=True):
            lang_tag = lang_map.get(lang_tag, lang_tag)
            try:
                sxng_tag = region_tag(babel.Locale.parse(f"{lang_tag}_{country_tag.upper()}"))
            except babel.UnknownLocaleError:
                # silently ignore unknown languages
                continue
            # print("%-20s: %s <-- %s" % (v["label"], country_tag, sxng_tag))

            conflict = engine_traits.regions.get(sxng_tag)
            if conflict and conflict != country_tag:
                print(f"CONFLICT: babel {sxng_tag} --> {conflict}, {country_tag}")
                continue
            engine_traits.regions[sxng_tag] = country_tag
