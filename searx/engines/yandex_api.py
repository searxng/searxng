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
set ``inactive: false`` and add your ``api_key`` and ``folder_id`` to
:origin:`searx/settings.yml`:

.. code:: yaml

  - name: yandex api
    engine: yandex_api
    shortcut: yda
    categories: [general, web]
    inactive: false
    api_key: ""           # Yandex Cloud API key (``Api-Key``)
    folder_id: ""         # Yandex Cloud folder id
    # optional, see below:
    search_type: SEARCH_TYPE_COM
    l10n: LOCALIZATION_EN

Implementations
===============

.. _Yandex Search API v2:
   https://yandex.cloud/en/docs/search-api/api-ref/WebSearch/search
.. _Yandex XML:
   https://yandex.com/dev/xml/doc/dg/concepts/response.html
"""

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
    "official_api_documentation": "https://yandex.cloud/en/docs/search-api/",
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
search_type: str = "SEARCH_TYPE_COM"
"""Search domain / type.  One of ``SEARCH_TYPE_RU`` (yandex.ru),
``SEARCH_TYPE_TR`` (yandex.com.tr), ``SEARCH_TYPE_KK`` (yandex.kz),
``SEARCH_TYPE_BE`` (yandex.by), ``SEARCH_TYPE_UZ`` (yandex.uz) or
``SEARCH_TYPE_COM`` (yandex.com, international)."""

l10n: str = "LOCALIZATION_EN"
"""Language of the search-result notifications.  One of ``LOCALIZATION_RU``,
``LOCALIZATION_BE``, ``LOCALIZATION_KK``, ``LOCALIZATION_UK``,
``LOCALIZATION_TR`` or ``LOCALIZATION_EN``."""

region: str = ""
"""Optional Yandex `region id`.
Only meaningful together with ``SEARCH_TYPE_RU``.

__ https://yandex.com/dev/xml/doc/dg/reference/regions.html
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

# Map a query language to a (search_type, l10n) pair.  Used to override the
# defaults when the request carries a matching language.
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
    if not api_key or not folder_id:
        raise SearxEngineAPIException("missing 'api_key' and/or 'folder_id' in engine settings")
    if not 1 <= page_size <= 100:
        raise SearxEngineAPIException("'page_size' must be in the range 1..100 (Yandex 'groupsOnPage')")

    global max_page  # pylint: disable=global-statement
    # ceiling division: the last (partial) page of the 250-result cap is valid
    max_page = -(-250 // page_size)
    return True


def request(query: str, params: "OnlineParams"):
    logger.debug("query: %r", query)  # pylint: disable=undefined-variable

    if len(query) > 400:
        # Yandex rejects a 'queryText' longer than 400 characters; decline the
        # request gracefully instead of provoking an API error.
        params["url"] = None
        return

    req_search_type = search_type
    req_l10n = l10n
    lang = params["searxng_locale"].split("-")[0].lower()
    if lang in language_map:
        req_search_type, req_l10n = language_map[lang]

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
        "folderId": folder_id,
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

    The synchronous endpoint returns ``{"rawData": "<base64>"}`` on success; HTTP
    errors are raised upstream via ``raise_for_httperror``.  The
    deferred/operation endpoint wraps the payload in ``{"response": {"rawData":
    ...}}`` and may carry an ``error`` object, which is surfaced defensively here.
    """
    data: dict[str, t.Any] = resp.json()

    error = data.get("error")
    if error:
        message = error.get("message", error) if isinstance(error, dict) else error
        raise SearxEngineAPIException(f"Yandex Search API error: {message}")

    raw_data = data.get("rawData")
    if raw_data is None:
        raw_data = data.get("response", {}).get("rawData")
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
