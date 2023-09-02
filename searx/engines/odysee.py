# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Odysee_ is a decentralised video hosting platform.

.. _Odysee: https://github.com/OdyseeTeam/odysee-frontend
"""

import time
from urllib.parse import urlencode
from datetime import datetime

# Engine metadata
about = {
    "website": "https://odysee.com/",
    "wikidata_id": "Q102046570",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

# Engine configuration
paging = True
results_per_page = 20
categories = ['videos']

# Search URL (Note: lighthouse.lbry.com/search works too, and may be faster at times)
base_url = "https://lighthouse.odysee.tv/search"


def request(query, params):
    start_index = (params["pageno"] - 1) * results_per_page
    query_params = {
        "s": query,
        "size": results_per_page,
        "from": start_index,
        "include": "channel,thumbnail_url,title,description,duration,release_time",
        "mediaType": "video",
    }

    params["url"] = f"{base_url}?{urlencode(query_params)}"
    return params


# Format the video duration
def format_duration(duration):
    seconds = int(duration)
    length = time.gmtime(seconds)
    if length.tm_hour:
        return time.strftime("%H:%M:%S", length)
    return time.strftime("%M:%S", length)


def response(resp):
    data = resp.json()
    results = []

    for item in data:
        name = item["name"]
        claim_id = item["claimId"]
        title = item["title"]
        thumbnail_url = item["thumbnail_url"]
        description = item["description"] or ""
        channel = item["channel"]
        release_time = item["release_time"]
        duration = item["duration"]

        release_date = datetime.strptime(release_time.split("T")[0], "%Y-%m-%d")
        formatted_date = datetime.utcfromtimestamp(release_date.timestamp())

        url = f"https://odysee.com/{name}:{claim_id}"
        iframe_url = f"https://odysee.com/$/embed/{name}:{claim_id}"
        odysee_thumbnail = f"https://thumbnails.odycdn.com/optimize/s:390:0/quality:85/plain/{thumbnail_url}"
        formatted_duration = format_duration(duration)

        results.append(
            {
                "title": title,
                "url": url,
                "content": description,
                "author": channel,
                "publishedDate": formatted_date,
                "length": formatted_duration,
                "thumbnail": odysee_thumbnail,
                "iframe_src": iframe_url,
                "template": "videos.html",
            }
        )

    return results
