# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Piratebay (Videos, Music, Files)
"""

from json import loads
from datetime import datetime
from operator import itemgetter

from urllib.parse import quote
from searx.utils import get_torrent_size

# about
about = {
    "website": 'https://thepiratebay.org',
    "wikidata_id": 'Q22663',
    "official_api_documentation": 'https://apibay.org/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ["files"]

# search-url
url = "https://thepiratebay.org/"
search_url = "https://apibay.org/q.php?q={search_term}&cat={search_type}"

# default trackers provided by thepiratebay
trackers = [
    "udp://tracker.coppersurfer.tk:6969/announce",
    "udp://9.rarbg.to:2920/announce",
    "udp://tracker.opentrackr.org:1337",
    "udp://tracker.internetwarriors.net:1337/announce",
    "udp://tracker.leechers-paradise.org:6969/announce",
    "udp://tracker.coppersurfer.tk:6969/announce",
    "udp://tracker.pirateparty.gr:6969/announce",
    "udp://tracker.cyberia.is:6969/announce",
]

# piratebay specific type-definitions
search_types = {"files": "0", "music": "100", "videos": "200"}


# do search-request
def request(query, params):
    search_type = search_types.get(params["category"], "0")

    params["url"] = search_url.format(search_term=quote(query), search_type=search_type)

    return params


# get response from search-request
def response(resp):
    results = []

    search_res = loads(resp.text)

    # return empty array if nothing is found
    if search_res[0]["name"] == "No results returned":
        return []

    # parse results
    for result in search_res:
        link = url + "description.php?id=" + result["id"]
        magnetlink = (
            "magnet:?xt=urn:btih:" + result["info_hash"] + "&dn=" + result["name"] + "&tr=" + "&tr=".join(trackers)
        )

        params = {
            "url": link,
            "title": result["name"],
            "seed": result["seeders"],
            "leech": result["leechers"],
            "magnetlink": magnetlink,
            "template": "torrent.html",
        }

        # extract and convert creation date
        try:
            date = datetime.fromtimestamp(float(result["added"]))
            params['publishedDate'] = date
        except:
            pass

        # let's try to calculate the torrent size
        try:
            filesize = get_torrent_size(result["size"], "B")
            params['filesize'] = filesize
        except:
            pass

        # append result
        results.append(params)

    # return results sorted by seeder
    return sorted(results, key=itemgetter("seed"), reverse=True)
