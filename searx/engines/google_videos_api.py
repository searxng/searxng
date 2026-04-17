# SPDX-License-Identifier: AGPL-3.0-or-later
"""Google Videos API engine using pluggable SERP API providers."""

from searx.engines.google_api_providers import (
    request_google_api,
    response_google_api,
    validate_google_api_config,
)

about = {
    "website": "https://www.google.com",
    "wikidata_id": "Q219885",
    "official_api_documentation": None,
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
}

categories = ["videos", "web"]
paging = True
time_range_support = True
safesearch = True
timeout = 10.0

provider = "serpbase"
api_key = ""


def init(_):
    validate_google_api_config(provider, api_key)


def request(query, params):
    request_google_api(
        query, params, provider=provider, api_key=api_key, search_type="videos"
    )
    return params


def response(resp):
    return response_google_api(resp, provider=provider, search_type="videos")
