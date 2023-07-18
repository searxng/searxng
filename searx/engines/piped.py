# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Piped (Videos)
"""

import time
import random
from urllib.parse import urlencode
from dateutil import parser

# about
about = {
    "website": 'https://github.com/TeamPiped/Piped/',
    "wikidata_id": 'Q107565255',
    "official_api_documentation": 'https://docs.piped.video/docs/api-documentation/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ["videos", "music"]
paging = False

# search-url
backend_url = "https://pipedapi.kavin.rocks"
frontend_url = "https://piped.video"


# do search-request
def request(query, params):
    if isinstance(backend_url, list):
        base_url = random.choice(backend_url)
    else:
        base_url = backend_url

    search_url = base_url + "/search?{query}&filter=videos"
    params["url"] = search_url.format(query=urlencode({'q': query}))

    return params


# get response from search-request
def response(resp):
    results = []

    search_results = resp.json()["items"]

    for result in search_results:
        publishedDate = parser.parse(time.ctime(result.get("uploaded", 0) / 1000))

        results.append(
            {
                # the api url differs from the frontend, hence use piped.video as default
                "url": frontend_url + result.get("url", ""),
                "title": result.get("title", ""),
                "content": result.get("shortDescription", ""),
                "template": "videos.html",
                "publishedDate": publishedDate,
                "iframe_src": frontend_url + '/embed' + result.get("url", ""),
                "thumbnail": result.get("thumbnail", ""),
            }
        )

    return results
