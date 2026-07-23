# SPDX-License-Identifier: AGPL-3.0-or-later
"""Engine to search using the official Exa Search API. Exa is a search engine for AI agents.

.. _Exa Search API: https://exa.ai/docs/reference/search

Configuration
=============

The engine has the following mandatory setting:

- :py:obj:`api_key`

Optional settings are:

- :py:obj:`results_per_page`
- :py:obj:`search_type`
- :py:obj:`content_mode`
- :py:obj:`content_max_characters`

.. code:: yaml

  - name: exaapi
    engine: exaapi
    api_key: "..."
    results_per_page: 10
    search_type: auto
    content_mode: highlights
    inactive: false

The API supports SafeSearch and region-aware results.
"""

import typing as t

from dateutil import parser

from searx.exceptions import SearxEngineAPIException
from searx.result_types import EngineResults
from searx.utils import html_to_text

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


SearchType = t.Literal["fast", "auto", "instant", "deep", "deep-lite", "deep-reasoning"]
ContentMode = t.Literal["highlights", "text"]

about = {
    "website": "https://exa.ai",
    "wikidata_id": None,
    "official_api_documentation": "https://exa.ai/docs/reference/search",
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
}

api_key: str = ""
"""API key for Exa Search API (required)."""

categories = ["general", "web"]
safesearch = True

base_url = "https://api.exa.ai/search"
results_per_page: int = 10
"""Maximum number of results per request. Value must be between 1 and 100, default is 10."""

search_type: SearchType = "auto"
"""Search type. Default is auto, see documentation for more information."""

content_mode: ContentMode = "highlights"
"""Content to request from the API: ``highlights`` (excerpts) or ``text`` (page text)."""

content_max_characters: int = 500
"""Maximum characters for the requested content."""


def init(_):
    if not api_key:
        raise SearxEngineAPIException("No API key provided")
    if not 1 <= results_per_page <= 100:
        raise ValueError("results_per_page must be between 1 and 100")
    if search_type not in t.get_args(SearchType):
        raise ValueError(f"Unsupported search type: {search_type}")
    if content_mode not in t.get_args(ContentMode):
        raise ValueError(f"Unsupported content mode: {content_mode}")
    if content_max_characters < 1:
        raise ValueError("content_max_characters must be at least 1")


def _contents_payload() -> dict[str, t.Any]:
    if content_mode == "text":
        return {"text": {"maxCharacters": content_max_characters, "stripLinks": True}}
    return {"highlights": {"maxCharacters": content_max_characters}}


def _extract_content(result: dict[str, t.Any]) -> str:
    if content_mode == "text":
        return html_to_text(result.get("text") or "")
    return html_to_text(" ".join(result.get("highlights") or []))


def request(query: str, params: "OnlineParams") -> None:
    """Create the API request."""
    body: dict[str, t.Any] = {
        "query": query,
        "type": search_type,
        "numResults": results_per_page,
        "contents": _contents_payload(),
    }

    # Apply SafeSearch if enabled
    if params["safesearch"]:
        body["moderation"] = True

    # Apply region-aware results if specified
    locale_parts = params["searxng_locale"].split("-")
    region = locale_parts[-1]
    if len(locale_parts) > 1:
        body["userLocation"] = region.upper()

    params["url"] = base_url
    params["method"] = "POST"
    params["headers"]["x-api-key"] = api_key
    params["json"] = body


def _extract_published_date(value: str | None):
    """Extract and parse the published date from the API response.

    Args:
        value: Raw date string from the API

    Returns:
        Parsed datetime object or None if parsing fails
    """
    if not value:
        return None
    try:
        return parser.parse(value)
    except (parser.ParserError, TypeError, OverflowError):
        return None


def response(resp: "SXNG_Response") -> EngineResults:
    """Process the API response and return results."""
    res = EngineResults()

    for result in resp.json().get("results", []):
        url = result.get("url")
        if not url:
            continue

        res.add(
            res.types.MainResult(
                url=url,
                title=html_to_text(result.get("title") or url),
                content=_extract_content(result),
                thumbnail=result.get("image") or "",
                publishedDate=_extract_published_date(result.get("publishedDate")),
                author=result.get("author") or "",
            )
        )

    return res
