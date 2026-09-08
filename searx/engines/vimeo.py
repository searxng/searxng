# SPDX-License-Identifier: AGPL-3.0-or-later
"""Vimeo (videos)"""

import typing as t
from datetime import datetime, timedelta
from urllib.parse import urlencode, urlparse
from searx.result_types import EngineResults
from searx.network import get
from searx.enginelib import EngineCache

# Engine metadata
about = {
    "website": 'https://vimeo.com/',
    "wikidata_id": 'Q156376',
    "official_api_documentation": 'http://developer.vimeo.com/api',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}


# Engine configuration
paging = True
categories = ['videos']
results_per_page = 20

# Search URL
base_url = "https://api.vimeo.com"

# Cache keys & expiration
JWT_CACHE_KEY = "jwt"
JWT_CACHE_EXPIRATION_SECONDS = 300

CACHE: EngineCache


def setup(engine_settings: dict[str, t.Any]) -> bool:
    global CACHE  # pylint: disable=global-statement
    CACHE = EngineCache(engine_settings["name"])


def fetch_json_web_token():

    if json_web_token := CACHE.get(JWT_CACHE_KEY):
        return json_web_token

    jwt_url = "https://vimeo.com/_next/jwt"

    jwt_headers = {
        'x-requested-with': "XMLHttpRequest",
    }

    resp = get(url=jwt_url, headers=jwt_headers, timeout=5)
    json_web_token = resp.json()["token"]

    CACHE.set(key=JWT_CACHE_KEY, value=json_web_token, expire=JWT_CACHE_EXPIRATION_SECONDS)

    return json_web_token


def request(query: str, params: "OnlineParams"):

    json_web_token = fetch_json_web_token()

    query_params = {
        "filter_type": "clip",
        "query": query,
        "page": params["pageno"],
        "per_page": results_per_page,
    }

    params["url"] = f"{base_url}/search?{urlencode(query_params)}"
    params["headers"]["content-type"] = "application/json"
    params["headers"]["authorization"] = "jwt " + json_web_token
    params["headers"]["Accept"] = "application/vnd.vimeo.*+json;version=3.3"


def response(resp: "SXNG_Response") -> EngineResults:
    results = EngineResults()
    search_res = resp.json()

    for item in search_res["data"]:

        video_id = urlparse(item["clip"]["link"]).path.strip('/')

        results.add(
            results.types.LegacyResult(
                template="videos.html",
                title=item["clip"]["name"],
                url=item["clip"]["link"],
                author=item["clip"]["user"]["name"],
                thumbnail=item["clip"]["pictures"]["base_link"],
                length=str(timedelta(seconds=item["clip"]["duration"])),
                publishedDate=datetime.fromisoformat(item["clip"]["created_time"]),
                iframe_src="https://player.vimeo.com/video/" + video_id,
            )
        )

    return results
