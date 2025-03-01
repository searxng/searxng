# SPDX-License-Identifier: AGPL-3.0-or-later
"""SoundCloud is a German audio streaming service."""

import re
from urllib.parse import quote_plus, urlencode
import datetime

from dateutil import parser
from lxml import html

from searx.network import get as http_get

about = {
    "website": "ttps://soundcloud.com",
    "wikidata_id": "Q568769",
    "official_api_documentation": "https://developers.soundcloud.com/docs/api/guide",
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ["music"]
paging = True

search_url = "https://api-v2.soundcloud.com/search"
"""This is not the offical (developer) url, it is the API which is used by the
HTML frontend of the common WEB site.
"""

cid_re = re.compile(r'client_id:"([^"]*)"', re.I | re.U)
guest_client_id = ""
results_per_page = 10

soundcloud_facet = "model"

app_locale_map = {
    "de": "de",
    "en": "en",
    "es": "es",
    "fr": "fr",
    "oc": "fr",
    "it": "it",
    "nl": "nl",
    "pl": "pl",
    "szl": "pl",
    "pt": "pt_BR",
    "pap": "pt_BR",
    "sv": "sv",
}


def request(query, params):

    # missing attributes: user_id, app_version
    # - user_id=451561-497874-703312-310156
    # - app_version=1740727428

    args = {
        "q": query,
        "offset": (params['pageno'] - 1) * results_per_page,
        "limit": results_per_page,
        "facet": soundcloud_facet,
        "client_id": guest_client_id,
        "app_locale": app_locale_map.get(params["language"].split("-")[0], "en"),
    }

    params['url'] = f"{search_url}?{urlencode(args)}"
    return params


def response(resp):
    results = []
    data = resp.json()

    for result in data.get("collection", []):

        if result["kind"] in ("track", "playlist"):
            url = result.get("permalink_url")
            if not url:
                continue
            uri = quote_plus(result.get("uri"))
            content = [
                result.get("description"),
                result.get("label_name"),
            ]
            res = {
                "url": url,
                "title": result["title"],
                "content": " / ".join([c for c in content if c]),
                "publishedDate": parser.parse(result["last_modified"]),
                "iframe_src": "https://w.soundcloud.com/player/?url=" + uri,
                "views": result.get("likes_count"),
            }
            thumbnail = result["artwork_url"] or result["user"]["avatar_url"]
            res["thumbnail"] = thumbnail or None
            length = int(result.get("duration", 0) / 1000)
            if length:
                length = datetime.timedelta(seconds=length)
                res["length"] = length
            res["views"] = result.get("playback_count", 0) or None
            res["author"] = result.get("user", {}).get("full_name") or None
            results.append(res)

    return results


def init(engine_settings=None):  # pylint: disable=unused-argument
    global guest_client_id  # pylint: disable=global-statement
    guest_client_id = get_client_id()


def get_client_id() -> str:

    client_id = ""
    url = "https://soundcloud.com"
    resp = http_get(url, timeout=10)

    if not resp.ok:
        logger.error("init: GET %s failed", url)
        return client_id

    tree = html.fromstring(resp.content)
    script_tags = tree.xpath("//script[contains(@src, '/assets/')]")
    app_js_urls = [tag.get("src") for tag in script_tags if tag is not None]

    # extracts valid app_js urls from soundcloud.com content

    for url in app_js_urls[::-1]:

        # gets app_js and search for the client_id
        resp = http_get(url)

        if not resp.ok:
            logger.error("init: app_js GET %s failed", url)
            continue

        cids = cid_re.search(resp.content.decode())
        if cids and len(cids.groups()):
            client_id = cids.groups()[0]
            break

    if client_id:
        logger.info("using client_id '%s' for soundclud queries", client_id)
    else:
        logger.warning("missing valid client_id for soundclud queries")
    return client_id
