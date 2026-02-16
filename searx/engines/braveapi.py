# SPDX-License-Identifier: AGPL-3.0-or-later
"""Engine to search using the Brave (WEB) Search API.

.. _Brave Search API: https://api-dashboard.search.brave.com/documentation

Configuration
=============

The engine has the following mandatory setting:

- :py:obj:`api_key`

Optional settings are:

- :py:obj:`results_per_page`

.. code:: yaml

  - name: braveapi
    engine: braveapi
    api_key: 'YOUR-API-KEY'  # required
    results_per_page: 20     # optional

The API supports paging and time filters.
"""

import typing as t

from urllib.parse import urlencode
from dateutil import parser

from searx.exceptions import SearxEngineAPIException
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://api.search.brave.com/",
    "wikidata_id": None,
    "official_api_documentation": "https://api-dashboard.search.brave.com/documentation",
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
}

api_key: str = ""
"""API key for Brave Search API (required)."""

categories = ["general", "web"]
paging = True
safesearch = True
time_range_support = True

results_per_page: int = 20
"""Maximum number of results per page (default 20)."""

base_url = "https://api.search.brave.com/res/v1/web/search"
"""Base URL for the Brave Search API."""

time_range_map = {"day": "past_day", "week": "past_week", "month": "past_month", "year": "past_year"}
"""Mapping of SearXNG time ranges to Brave API time ranges."""


def init(_):
    """Initialize the engine."""
    if not api_key:
        raise SearxEngineAPIException("No API key provided")


def request(query: str, params: "OnlineParams") -> None:
    """Create the API request."""
    search_args: dict[str, str | int | None] = {
        "q": query,
        "count": results_per_page,
        "offset": (params["pageno"] - 1) * results_per_page,
    }

    # Apply time filter if specified
    if params["time_range"]:
        search_args["time_range"] = time_range_map.get(params["time_range"])

    # Apply SafeSearch if enabled
    if params["safesearch"]:
        search_args["safesearch"] = "strict"

    params["url"] = f"{base_url}?{urlencode(search_args)}"
    params["headers"]["X-Subscription-Token"] = api_key


def _extract_published_date(published_date_raw: str):
    """Extract and parse the published date from the API response.

    Args:
        published_date_raw: Raw date string from the API

    Returns:
        Parsed datetime object or None if parsing fails
    """
    if not published_date_raw:
        return None

    try:
        return parser.parse(published_date_raw)
    except parser.ParserError:
        return None


def response(resp: "SXNG_Response") -> EngineResults:
    """Process the API response and return results."""
    res = EngineResults()
    data = resp.json()

    for result in data.get("web", {}).get("results", []):
        res.add(
            res.types.MainResult(
                url=result["url"],
                title=result["title"],
                content=result.get("description", ""),
                publishedDate=_extract_published_date(result.get("age")),
                thumbnail=result.get("thumbnail", {}).get("src"),
            ),
        )

    return res
