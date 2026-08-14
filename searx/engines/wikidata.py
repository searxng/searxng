# SPDX-License-Identifier: AGPL-3.0-or-later
"""This module implements the Wikidata engine.

Some implementations are shared from :ref:`wikipedia engine`.
"""
# pylint: disable=missing-class-docstring

import typing as t

from hashlib import md5
from urllib.parse import urlencode, unquote
from json import loads


from searx.network import post, get
from searx.utils import get_string_replaces_function
from searx.external_urls import area_to_osm_zoom
from searx.engines.wikipedia import (
    fetch_wikimedia_traits,
    get_wiki_params,
)
from searx.enginelib.traits import EngineTraits
from searx.wikidata_properties import (
    QUERY_TEMPLATE,
    WDArticle,
    WDAttrList,
    WDGeoAttribute,
    WDImageAttribute,
    WDURLAttribute,
    get_attributes,
)
from searx.wikidata import SPARQL_ENDPOINT_URL, SPARQL_EXPLAIN_URL, get_wikidata_headers

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


# about
about = {
    "website": 'https://wikidata.org/',
    "wikidata_id": 'Q2013',
    "official_api_documentation": 'https://query.wikidata.org/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}
language_support = True

display_type = ["infobox"]
"""A list of display types composed from ``infobox`` and ``list``.  The latter
one will add a hit to the result list.  The first one will show a hit in the
info box.  Both values can be set, or one of the two can be set."""

# see the property "dummy value" of https://www.wikidata.org/wiki/Q2013 (Wikidata)
# hard coded here to avoid to an additional SPARQL request when the server starts
DUMMY_ENTITY_URLS = set(
    "http://www.wikidata.org/entity/" + wid for wid in ("Q4115189", "Q13406268", "Q15397819", "Q17339402")
)


# https://www.w3.org/TR/sparql11-query/#rSTRING_LITERAL1
# https://lists.w3.org/Archives/Public/public-rdf-dawg/2011OctDec/0175.html
sparql_string_escape = get_string_replaces_function(
    # fmt: off
    {"\t": "\\\t", "\n": "\\\n", "\r": "\\\r", "\b": "\\\b", "\f": "\\\f", "\"": "\\\"", "'": "\\'", "\\": "\\\\"}
    # fmt: on
)

replace_http_by_https = get_string_replaces_function({"http:": "https:"})


def request(query: str, params: "OnlineParams") -> None:

    attributes: WDAttrList
    eng_tag, _wiki_netloc = get_wiki_params(params["searxng_locale"], traits)
    query, attributes = get_query(query, eng_tag or "en")
    logger.debug("request --> language %s // len(attributes): %s", eng_tag, len(attributes))

    params["method"] = "POST"
    params["url"] = SPARQL_ENDPOINT_URL
    params["data"] = {"query": query}
    params["headers"] = get_wikidata_headers()

    # additional parameters (not a part of OnlineParams)
    params["language"] = eng_tag  # type: ignore
    params["attributes"] = attributes  # type: ignore


def response(resp: "SXNG_Response") -> list[dict[str, t.Any]]:

    results: list[dict[str, t.Any]] = []
    jsonresponse = loads(resp.content.decode())

    # additional parameters ..
    language: str = resp.search_params["language"]  # type: ignore
    attributes: WDAttrList = resp.search_params["attributes"]  # type: ignore

    logger.debug("request --> language %s // len(attributes): %s", language, len(attributes))

    seen_entities: set[str] = set()
    for result in jsonresponse.get("results", {}).get("bindings", []):
        attribute_result = {key: value["value"] for key, value in result.items()}
        entity_url: str = attribute_result["item"]
        if entity_url not in seen_entities and entity_url not in DUMMY_ENTITY_URLS:
            seen_entities.add(entity_url)
            results += get_results(attribute_result, attributes, language)
        else:
            logger.debug("The SPARQL request returns duplicate entities: %s", str(attribute_result))

    return results


_IMG_SRC_DEFAULT_URL_PREFIX = "https://commons.wikimedia.org/wiki/Special:FilePath/"
_IMG_SRC_NEW_URL_PREFIX = "https://upload.wikimedia.org/wikipedia/commons/thumb/"


def get_thumbnail(img_src: str | None) -> str | None:
    """Get Thumbnail image from wikimedia commons

    Images from commons.wikimedia.org are (HTTP) redirected to
    upload.wikimedia.org.  The redirected URL can be calculated by this
    function.

    - https://stackoverflow.com/a/33691240

    """
    logger.debug("get_thumbnail(): %s", img_src)
    if not img_src is None and _IMG_SRC_DEFAULT_URL_PREFIX in img_src.split()[0]:
        img_src_name = unquote(img_src.replace(_IMG_SRC_DEFAULT_URL_PREFIX, "").split("?", 1)[0].replace("%20", "_"))
        img_src_name_first = img_src_name
        img_src_name_second = img_src_name

        if ".svg" in img_src_name.split()[0]:
            img_src_name_second = img_src_name + ".png"

        img_src_size = img_src.replace(_IMG_SRC_DEFAULT_URL_PREFIX, "").split("?", 1)[1]
        img_src_size = img_src_size[img_src_size.index("=") + 1 : img_src_size.index("&")]
        img_src_name_md5 = md5(img_src_name.encode("utf-8")).hexdigest()
        img_src = (
            _IMG_SRC_NEW_URL_PREFIX
            + img_src_name_md5[0]
            + "/"
            + img_src_name_md5[0:2]
            + "/"
            + img_src_name_first
            + "/"
            + img_src_size
            + "px-"
            + img_src_name_second
        )
        logger.debug("get_thumbnail() redirected: %s", img_src)

    return img_src


def get_results(
    attribute_result: dict[str, t.Any],
    attributes: WDAttrList,
    language: str,
):
    # pylint: disable=too-many-branches
    results: list[dict[str, t.Any]] = []
    infobox_title: str = attribute_result.get("itemLabel")  # pyright: ignore[reportAssignmentType]
    infobox_id = attribute_result["item"]
    infobox_id_lang: str | None = None
    infobox_urls: list[dict[str, str]] = []
    infobox_attributes: list[dict[str, str]] = []
    infobox_content = attribute_result.get("itemDescription", [])
    img_src: str | None = None
    img_src_priority = 0

    for attribute in attributes:
        value: str | None = attribute.get_str(attribute_result, language)
        if value is not None and value != "":
            if isinstance(attribute, (WDURLAttribute, WDArticle)):
                # get_select() method : there is group_concat(distinct ...;separator=", ")
                # split the value here
                for url in value.split(", "):
                    infobox_urls.append({"title": attribute.get_label(language), "url": url, **attribute.kwargs})
                    # "normal" results (not infobox) include official website and Wikipedia links.
                    if "list" in display_type and (
                        attribute.kwargs.get("official") or isinstance(attribute, WDArticle)
                    ):
                        results.append({"title": infobox_title, "url": url, "content": infobox_content})

                    # update the infobox_id with the wikipedia URL
                    # first the local wikipedia URL, and as fallback the english wikipedia URL
                    if isinstance(attribute, WDArticle) and (
                        (attribute.language == "en" and infobox_id_lang is None) or attribute.language != "en"
                    ):
                        infobox_id_lang = attribute.language
                        infobox_id = url
            elif isinstance(attribute, WDImageAttribute):
                # this attribute is an image.
                # replace the current image only the priority is lower
                # (the infobox contain only one image).
                if attribute.priority > img_src_priority:
                    img_src = get_thumbnail(value)
                    img_src_priority = attribute.priority
            elif isinstance(attribute, WDGeoAttribute):
                # geocoordinate link
                # use the area to get the OSM zoom
                # Note: ignore the unit (must be km² otherwise the calculation is wrong)
                # Should use normalized value p:P2046/psn:P2046/wikibase:quantityAmount
                area = attribute_result.get("P2046")
                osm_zoom: int = area_to_osm_zoom(area) if area else 19
                url = attribute.get_geo_url(attribute_result, osm_zoom=osm_zoom)
                if url:
                    infobox_urls.append({"title": attribute.get_label(language), "url": url, "entity": attribute.name})
            else:
                infobox_attributes.append(
                    {"label": attribute.get_label(language), "value": value, "entity": attribute.name}
                )

    if infobox_id:
        infobox_id = replace_http_by_https(infobox_id)

    # add the wikidata URL at the end
    infobox_urls.append({"title": "Wikidata", "url": attribute_result["item"]})

    if (
        "list" in display_type
        and img_src is None
        and len(infobox_attributes) == 0
        and len(infobox_urls) == 1
        and len(infobox_content) == 0
    ):
        results.append({"url": infobox_urls[0]["url"], "title": infobox_title, "content": infobox_content})
    elif "infobox" in display_type:
        results.append(
            {
                "infobox": infobox_title,
                "id": infobox_id,
                "content": infobox_content,
                "img_src": img_src,
                "urls": infobox_urls,
                "attributes": infobox_attributes,
            }
        )
    return results


def get_query(query: str, language: str) -> tuple[str, WDAttrList]:
    attributes = get_attributes(language)
    select = [a.get_select() for a in attributes]
    where = list(filter(lambda s: len(s) > 0, [a.get_where() for a in attributes]))
    wikibase_label = list(filter(lambda s: len(s) > 0, [a.get_wikibase_label() for a in attributes]))
    group_by = list(filter(lambda s: len(s) > 0, [a.get_group_by() for a in attributes]))
    query = (
        QUERY_TEMPLATE.replace("%QUERY%", sparql_string_escape(query))
        .replace("%SELECT%", " ".join(select))
        .replace("%WHERE%", "\n  ".join(where))
        .replace("%WIKIBASE_LABELS%", "\n      ".join(wikibase_label))
        .replace("%GROUP_BY%", " ".join(group_by))
        .replace("%LANGUAGE%", language)
    )
    return query, attributes


def debug_explain_wikidata_query(query: str, method: str = "GET"):
    if method == "GET":
        http_response = get(SPARQL_EXPLAIN_URL + "&" + urlencode({"query": query}), headers=get_wikidata_headers())
    else:
        http_response = post(SPARQL_EXPLAIN_URL, data={"query": query}, headers=get_wikidata_headers())
    http_response.raise_for_status()
    return http_response.content


def fetch_traits(engine_traits: EngineTraits):
    """Uses languages evaluated from :py:obj:`wikipedia.fetch_wikimedia_traits
    <searx.engines.wikipedia.fetch_wikimedia_traits>` and removes

    - ``traits.custom['wiki_netloc']``: wikidata does not have net-locations for
      the languages and the list of all

    - ``traits.custom['WIKIPEDIA_LANGUAGES']``: not used in the wikipedia engine

    """

    fetch_wikimedia_traits(engine_traits)
    engine_traits.custom["wiki_netloc"] = {}
    engine_traits.custom["WIKIPEDIA_LANGUAGES"] = []
