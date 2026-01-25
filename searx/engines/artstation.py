# SPDX-License-Identifier: AGPL-3.0-or-later
"""Artstation (images)"""

import re
import typing as t
from json import dumps

from searx.result_types import EngineResults
from searx.network import post
from searx.enginelib import EngineCache

# Engine metadata
about = {
    "website": 'https://www.artstation.com/',
    "wikidata_id": 'Q65551500',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

# Engine configuration
paging = True
categories = ['images']
results_per_page = 20

# Search URL
base_url = "https://www.artstation.com/api/v2/search/projects.json"

# Cache keys & expiration
CSRF_PUBLICKEY_CACHE = "public_csrf_token"
CSRF_PRIVATEKEY_CACHE = "private_csrf_token"
KEY_EXPIRATION_SECONDS = 3600

CACHE: EngineCache


def setup(engine_settings: dict[str, t.Any]) -> bool:
    global CACHE  # pylint: disable=global-statement
    CACHE = EngineCache(engine_settings["name"])
    return True


def fetch_csrf_tokens():

    public_token: str | None = CACHE.get(CSRF_PUBLICKEY_CACHE)
    private_token: str | None = CACHE.get(CSRF_PRIVATEKEY_CACHE)

    if public_token and private_token:
        return public_token, private_token

    resp = post("https://www.artstation.com/api/v2/csrf_protection/token.json")
    public_token = resp.json()["public_csrf_token"]
    private_token = resp.cookies["PRIVATE-CSRF-TOKEN"]

    CACHE.set(key=CSRF_PUBLICKEY_CACHE, value=public_token, expire=KEY_EXPIRATION_SECONDS)
    CACHE.set(key=CSRF_PRIVATEKEY_CACHE, value=private_token, expire=KEY_EXPIRATION_SECONDS)

    return public_token, private_token


def request(query, params):

    public_token, private_token = fetch_csrf_tokens()

    form_data = {
        "query": query,
        "page": params["pageno"],
        "per_page": results_per_page,
        "sorting": "relevance",
        "pro_first": 1,
    }

    params["url"] = base_url
    params["method"] = 'POST'
    params['headers']['content-type'] = "application/json"
    params['headers']['PUBLIC-CSRF-TOKEN'] = public_token
    params["cookies"] = {"PRIVATE-CSRF-TOKEN": private_token}
    params['data'] = dumps(form_data)

    return params


def response(resp) -> EngineResults:
    results = EngineResults()
    search_res = resp.json()

    for item in search_res["data"]:
        thumb = item["smaller_square_cover_url"]
        fullsize_image = re.sub(r'/\d{6,}/', '/', thumb).replace("smaller_square", "large")

        results.add(
            results.types.LegacyResult(
                {
                    "template": 'images.html',
                    "title": item["title"],
                    "url": item["url"],
                    "author": f"{item['user']['username']} ({item['user']['full_name']})",
                    "img_src": fullsize_image,
                    "thumbnail_src": thumb,
                }
            )
        )

    return results
