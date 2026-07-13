# SPDX-License-Identifier: AGPL-3.0-or-later
"""Yandex Search API (the official **paid** `Yandex Search API v2`_).

Unlike the :origin:`yandex <searx/engines/yandex.py>` engine (which scrapes the
public HTML interface and is prone to CAPTCHA blocking), this engine talks to
the official, paid Yandex Cloud Search API.  It requires a Yandex Cloud account,
a *folder id* and an *API key*.

The API answers with a Base64 encoded XML document in the classic
`Yandex XML`_ format which is decoded and parsed here.

Configuration
=============

The engine is inactive by default because it needs credentials.  To enable it,
set ``inactive: false`` and add your ``api_key`` and ``yandex_folder_id`` to
:origin:`searx/settings.yml`:

.. code:: yaml

  - name: yandex api
    engine: yandex_api
    shortcut: yda
    categories: [general, web]
    inactive: false
    api_key: ""           # Yandex Cloud API key (``Api-Key``)
    yandex_folder_id: ""  # Yandex Cloud folder id
    # optional, see below:
    yandex_default_language: en

Implementations
===============

.. _Yandex Search API v2:
   https://aistudio.yandex.ru/docs/en/search-api/api-ref/WebSearch/search.html
"""

import math
import typing as t
from base64 import b64decode

from lxml import etree

from searx.exceptions import SearxEngineAPIException
from searx.result_types import EngineResults
from searx.utils import extract_text

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://yandex.cloud/en/services/search-api",
    "wikidata_id": "Q5281",
    "official_api_documentation": "https://aistudio.yandex.ru/docs/en/search-api/api-ref/WebSearch/search.html",
    "use_official_api": True,
    "require_api_key": True,
    "results": "XML",
}

# Engine configuration
categories = ["general", "web"]
paging = True
safesearch = True

# A query returns at most 250 results, so the number of reachable pages depends
# on ``page_size`` (25 for the default of 10).  The exact value -- rounding the
# last, partial page up -- is (re)computed in setup().
max_page = 25

# Credentials, overwritten via settings.yml
api_key: str = ""
"""Yandex Cloud API key, passed as ``Authorization: Api-Key <api_key>``."""

yandex_folder_id: str = ""
"""Yandex Cloud folder id the API key belongs to."""

# Search tuning, overwritten via settings.yml
yandex_default_language: str = "en"
"""Default query language.  It selects the Yandex search domain (e.g. yandex.ru
for ``ru``, yandex.com for ``en``) and the language of the search-result
notifications, but only as a fallback -- a request whose own locale matches
:py:obj:`language_map` overrides it.  Must be one of its keys: ``ru``, ``be``,
``kk``, ``uk``, ``tr`` or ``en``."""

region: str = ""
"""Optional Yandex `region id`.
Only meaningful together with ``SEARCH_TYPE_RU``.

__ https://aistudio.yandex.ru/docs/en/search-api/reference/regions.html
"""

page_size: int = 10
"""Number of results requested per page."""

base_url = "https://searchapi.api.cloud.yandex.net/v2/web/search"

# searxng safesearch level -> Yandex familyMode
safesearch_map = {
    0: "FAMILY_MODE_NONE",
    1: "FAMILY_MODE_MODERATE",
    2: "FAMILY_MODE_STRICT",
}

# Map a query language to a (search_type, l10n) pair.  It drives both the
# per-request override (when the query's locale matches) and the
# ``yandex_default_language`` default.
language_map = {
    "ru": ("SEARCH_TYPE_RU", "LOCALIZATION_RU"),
    "be": ("SEARCH_TYPE_BE", "LOCALIZATION_BE"),
    "kk": ("SEARCH_TYPE_KK", "LOCALIZATION_KK"),
    "uk": ("SEARCH_TYPE_RU", "LOCALIZATION_UK"),
    "tr": ("SEARCH_TYPE_TR", "LOCALIZATION_TR"),
    "en": ("SEARCH_TYPE_COM", "LOCALIZATION_EN"),
    # Uzbek ('uz') is intentionally omitted: Yandex offers SEARCH_TYPE_UZ but no
    # matching LOCALIZATION_UZ, so such queries fall back to the defaults above.
}


def setup(_) -> bool:
    """Validate credentials and paging limits when the engine is loaded."""
    if not api_key or not yandex_folder_id:
        raise SearxEngineAPIException("missing 'api_key' and/or 'yandex_folder_id' in engine settings")
    if not 1 <= page_size <= 100:
        raise SearxEngineAPIException("'page_size' must be in the range 1..100 (Yandex 'groupsOnPage')")
    if yandex_default_language not in language_map:
        raise SearxEngineAPIException(f"'yandex_default_language' must be one of {sorted(language_map)}")

    global max_page  # pylint: disable=global-statement
    # round up: the last (partial) page of the 250-result cap is still reachable
    max_page = math.ceil(250 / page_size)
    return True


def request(query: str, params: "OnlineParams"):

    if len(query) > 400:
        # Yandex rejects a 'queryText' longer than 400 characters; decline the
        # request gracefully instead of provoking an API error.
        params["url"] = None
        return

    lang = params["searxng_locale"].split("-")[0].lower()
    req_search_type, req_l10n = language_map.get(lang, language_map[yandex_default_language])

    body: dict[str, t.Any] = {
        "query": {
            "searchType": req_search_type,
            "queryText": query,
            "familyMode": safesearch_map[params["safesearch"]],
            # the API uses a 0-based page index
            "page": str(params["pageno"] - 1),
        },
        "groupSpec": {
            "groupMode": "GROUP_MODE_FLAT",
            "groupsOnPage": str(page_size),
            "docsInGroup": "1",
        },
        "l10n": req_l10n,
        "folderId": yandex_folder_id,
        "responseFormat": "FORMAT_XML",
    }
    # Yandex accepts a 'region' only together with the Russian search type.
    if region and req_search_type == "SEARCH_TYPE_RU":
        body["region"] = region

    params["method"] = "POST"
    params["url"] = base_url
    params["headers"]["Authorization"] = f"Api-Key {api_key}"
    params["headers"]["Content-Type"] = "application/json"
    params["json"] = body


def _raw_xml(resp: "SXNG_Response") -> bytes:
    """Extract and Base64-decode the XML payload out of the JSON envelope.

    The synchronous ``/v2/web/search`` endpoint returns ``{"rawData":
    "<base64>"}`` on success; HTTP errors are raised upstream via
    ``raise_for_httperror``.
    """
    data: dict[str, t.Any] = resp.json()

    raw_data = data.get("rawData")
    if raw_data is None:
        raise SearxEngineAPIException("Yandex Search API: no 'rawData' in response")

    return b64decode(raw_data)


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()

    dom = etree.fromstring(_raw_xml(resp))  # pylint: disable=c-extension-no-member

    # An <error> inside <response> signals an application error.  Code 15 simply
    # means "nothing was found" and must not raise.
    error = dom.find(".//response/error")
    if error is not None:
        if error.get("code") == "15":
            return res
        raise SearxEngineAPIException(f"Yandex Search API error {error.get('code')}: {error.text}")

    for doc in dom.iterfind(".//doc"):
        url = extract_text(doc.find("url"), allow_none=True)
        title = extract_text(doc.find("title"), allow_none=True)
        if not url or not title:
            continue

        content = extract_text(doc.find("headline"), allow_none=True)
        if not content:
            passages = doc.find("passages")
            if passages is not None:
                content = " ".join(extract_text(p) or "" for p in passages.iterfind("passage")).strip()

        res.add(
            res.types.MainResult(
                url=url,
                title=title,
                content=content or "",
            )
        )

    return res
