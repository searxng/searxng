# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Solid Torrents

"""

from json import loads
from urllib.parse import urlencode

about = {
    "website": 'https://www.solidtorrents.net/',
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ['files']
paging = True

base_url = 'https://www.solidtorrents.net/'
search_url = base_url + 'api/v1/search?{query}'


def request(query, params):
    skip = (params['pageno'] - 1) * 20
    query = urlencode({'q': query, 'skip': skip})
    params['url'] = search_url.format(query=query)
    logger.debug("query_url --> %s", params['url'])
    return params


def response(resp):
    results = []
    search_results = loads(resp.text)

    for result in search_results["results"]:
        results.append({
            'infohash': result["infohash"],
            'seed': result["swarm"]["seeders"],
            'leech': result["swarm"]["leechers"],
            'title': result["title"],
            'url': "https://solidtorrents.net/view/" + result["_id"],
            'filesize': result["size"],
            'magnetlink': result["magnet"],
            'template': "torrent.html",
        })
    return results
