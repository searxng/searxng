# SPDX-License-Identifier: AGPL-3.0-or-later
"""Engine to search using the official `Tavily Search API`_. Tavily is a search
API optimized for LLMs and AI agents.

.. _Tavily Search API: https://docs.tavily.com/documentation/api-reference/endpoint/search

Configuration
=============

The engine has the following mandatory setting:

- :py:obj:`api_key`

You can obtain an API key from the `Tavily dashboard <https://app.tavily.com/home>`_.


Optional settings are:

- :py:obj:`results_per_page`
- :py:obj:`search_depth`
- :py:obj:`topic`

.. code:: yaml

  - name: tavily
    engine: tavily
    shortcut: tvy
    api_key: "tvly-..."
    results_per_page: 10
    search_depth: basic
    topic: general
    inactive: false

The API supports SafeSearch (Enterprise feature) and time range filters.
"""

import typing as t

from dateutil import parser

from searx.exceptions import SearxEngineAPIException
from searx.result_types import EngineResults
from searx.utils import html_to_text

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


SearchDepth = t.Literal["basic", "advanced", "fast", "ultra-fast"]
Topic = t.Literal["general", "news", "finance"]

about = {
    "website": "https://www.tavily.com",
    "wikidata_id": None,
    "official_api_documentation": "https://docs.tavily.com/documentation/api-reference/endpoint/search",
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
}

api_key: str = ""
"""API key for Tavily Search API (required)."""

categories = ["general", "web"]
safesearch = True
time_range_support = True

base_url = "https://api.tavily.com/search"

page_size: int = 10
"""Maximum number of results per request. Value must be between 1 and 20, default is 10."""

search_depth: SearchDepth = "basic"
"""Search depth: ``basic``, ``advanced``, ``fast`` or ``ultra-fast``. Default is ``basic``."""

topic: Topic = "general"
"""Search topic: ``general``, ``news`` or ``finance``. Default is ``general``."""


def init(_):
    if not api_key:
        raise SearxEngineAPIException("No API key provided")
    if not 1 <= results_per_page <= 20:
        raise ValueError("results_per_page must be between 1 and 20")
    if search_depth not in t.get_args(SearchDepth):
        raise ValueError(f"Unsupported search_depth: {search_depth}")
    if topic not in t.get_args(Topic):
        raise ValueError(f"Unsupported topic: {topic}")


def request(query: str, params: "OnlineParams") -> None:
    """Create the API request."""
    body: dict[str, t.Any] = {
        "query": query,
        "search_depth": search_depth,
        "topic": topic,
        "max_results": results_per_page,
        "include_answer": False,
        "include_raw_content": False,
        "include_images": False,
    }

    # SearXNG time ranges (day/week/month/year) map 1:1 to Tavily's time_range values
    if params["time_range"]:
        body["time_range"] = params["time_range"]

    # Safe search is currently a Tavily Enterprise feature
    if params["safesearch"]:
        body["safe_search"] = True

    params["url"] = base_url
    params["method"] = "POST"
    params["headers"]["Authorization"] = f"Bearer {api_key}"
    params["headers"]["Content-Type"] = "application/json"
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

    for item in resp.json().get("results", []):
        url = item.get("url")
        if not url:
            continue

        res.add(
            res.types.MainResult(
                url=url,
                title=html_to_text(item.get("title") or url),
                content=html_to_text(item.get("content") or ""),
                publishedDate=_extract_published_date(item.get("published_date")),
            )
        )

    return res
