# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Odysee_ is a decentralized video hosting platform.

.. _Odysee: https://github.com/OdyseeTeam/odysee-frontend
"""

import time
from urllib.parse import urlencode
from datetime import datetime

import babel

from searx.network import get
from searx.locales import language_tag
from searx.enginelib.traits import EngineTraits

traits: EngineTraits

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
time_range_support = True
results_per_page = 20
categories = ['videos']

# Search URL (Note: lighthouse.lbry.com/search works too, and may be faster at times)
base_url = "https://lighthouse.odysee.tv/search"


def request(query, params):
    time_range_dict = {
        "day": "today",
        "week": "thisweek",
        "month": "thismonth",
        "year": "thisyear",
    }

    start_index = (params["pageno"] - 1) * results_per_page
    query_params = {
        "s": query,
        "size": results_per_page,
        "from": start_index,
        "include": "channel,thumbnail_url,title,description,duration,release_time",
        "mediaType": "video",
    }

    lang = traits.get_language(params['searxng_locale'], None)
    if lang is not None:
        query_params['language'] = lang

    if params['time_range'] in time_range_dict:
        query_params['time_filter'] = time_range_dict[params['time_range']]

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


def fetch_traits(engine_traits: EngineTraits):
    """
    Fetch languages from Odysee's source code.
    """

    resp = get(
        'https://raw.githubusercontent.com/OdyseeTeam/odysee-frontend/master/ui/constants/supported_browser_languages.js',  # pylint: disable=line-too-long
        timeout=60,
    )

    if not resp.ok:
        print("ERROR: can't determine languages from Odysee")
        return

    for line in resp.text.split("\n")[1:-4]:
        lang_tag = line.strip().split(": ")[0].replace("'", "")

        try:
            sxng_tag = language_tag(babel.Locale.parse(lang_tag, sep="-"))
        except babel.UnknownLocaleError:
            print("ERROR: %s is unknown by babel" % lang_tag)
            continue

        conflict = engine_traits.languages.get(sxng_tag)
        if conflict:
            if conflict != lang_tag:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_tag, conflict, lang_tag))
            continue

        engine_traits.languages[sxng_tag] = lang_tag
