# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Invidious (Videos)
"""

import time
import random
from urllib.parse import quote_plus
from dateutil import parser

# about
about = {
    "website": 'https://api.invidious.io/',
    "wikidata_id": 'Q79343316',
    "official_api_documentation": 'https://github.com/iv-org/documentation/blob/master/API.md',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ["videos", "music"]
paging = True
time_range_support = True

# base_url can be overwritten by a list of URLs in the settings.yml
base_url = 'https://vid.puffyan.us'


def request(query, params):
    time_range_dict = {
        "day": "today",
        "week": "week",
        "month": "month",
        "year": "year",
    }

    if isinstance(base_url, list):
        params["base_url"] = random.choice(base_url)
    else:
        params["base_url"] = base_url

    search_url = params["base_url"] + "/api/v1/search?q={query}"
    params["url"] = search_url.format(query=quote_plus(query)) + "&page={pageno}".format(pageno=params["pageno"])

    if params["time_range"] in time_range_dict:
        params["url"] += "&date={timerange}".format(timerange=time_range_dict[params["time_range"]])

    if params["language"] != "all":
        lang = params["language"].split("-")
        if len(lang) == 2:
            params["url"] += "&range={lrange}".format(lrange=lang[1])

    return params


def response(resp):
    results = []

    search_results = resp.json()
    base_invidious_url = resp.search_params['base_url'] + "/watch?v="

    for result in search_results:
        rtype = result.get("type", None)
        if rtype == "video":
            videoid = result.get("videoId", None)
            if not videoid:
                continue

            url = base_invidious_url + videoid
            thumbs = result.get("videoThumbnails", [])
            thumb = next((th for th in thumbs if th["quality"] == "sddefault"), None)
            if thumb:
                thumbnail = thumb.get("url", "")
            else:
                thumbnail = ""

            publishedDate = parser.parse(time.ctime(result.get("published", 0)))
            length = time.gmtime(result.get("lengthSeconds"))
            if length.tm_hour:
                length = time.strftime("%H:%M:%S", length)
            else:
                length = time.strftime("%M:%S", length)

            results.append(
                {
                    "url": url,
                    "title": result.get("title", ""),
                    "content": result.get("description", ""),
                    'length': length,
                    "template": "videos.html",
                    "author": result.get("author"),
                    "publishedDate": publishedDate,
                    "iframe_src": resp.search_params['base_url'] + '/embed/' + videoid,
                    "thumbnail": thumbnail,
                }
            )

    return results
