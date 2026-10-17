# SPDX-License-Identifier: AGPL-3.0-or-later
"""Odysee_ is a decentralized video hosting platform.

.. _Odysee: https://github.com/OdyseeTeam/odysee-frontend
"""

import typing as t
from datetime import datetime, timedelta
from urllib.parse import urlencode

import babel

from searx.enginelib.traits import EngineTraits
from searx.locales import language_tag
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

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
language_support = True
results_per_page = 20
categories = ["videos"]

# Search URL (Note: lighthouse.lbry.com/search works too, and may be faster at times)
base_url = "https://lighthouse.odysee.tv/search"


def request(query: str, params: "OnlineParams"):
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

    lang = traits.get_language(params["searxng_locale"], None)
    if lang is not None:
        query_params["language"] = lang

    if params["time_range"] in time_range_dict:
        query_params["time_filter"] = time_range_dict[params["time_range"]]

    params["url"] = f"{base_url}?{urlencode(query_params)}"


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()
    data = resp.json()

    for item in data:
        name = item["name"]
        claim_id = item["claimId"]
        thumbnail_url = item["thumbnail_url"]
        release_time = item["release_time"]

        release_date = datetime.fromisoformat(release_time.split("T")[0])
        formatted_date = datetime.fromtimestamp(release_date.timestamp())

        url = f"https://odysee.com/{name}:{claim_id}"
        iframe_url = f"https://odysee.com/$/embed/{name}:{claim_id}"
        odysee_thumbnail = f"https://thumbnails.odycdn.com/optimize/s:390:0/quality:85/plain/{thumbnail_url}"

        res.add(
            res.types.Video(
                title=item["title"],
                url=url,
                content=item["description"] or "",
                author=item["channel"],
                publishedDate=formatted_date,
                length=timedelta(seconds=item["duration"]),
                thumbnail=odysee_thumbnail,
                iframe_src=iframe_url,
            )
        )

    return res


def fetch_traits(engine_traits: EngineTraits):
    """
    Fetch languages from Odysee's source code.
    """
    # pylint: disable=import-outside-toplevel

    from searx.network import get  # see https://github.com/searxng/searxng/issues/762

    resp = get(
        "https://raw.githubusercontent.com/OdyseeTeam/odysee-frontend/master/ui/constants/supported_browser_languages.js",  # pylint: disable=line-too-long
        timeout=5,
    )
    if not resp.ok:
        raise RuntimeError("Response from Odysee is not OK.")

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
