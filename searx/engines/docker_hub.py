# SPDX-License-Identifier: AGPL-3.0-or-later
"""Docker Hub (IT)

"""
# pylint: disable=use-dict-literal

from urllib.parse import urlencode
from dateutil import parser

about = {
    "website": 'https://hub.docker.com',
    "wikidata_id": 'Q100769064',
    "official_api_documentation": 'https://docs.docker.com/registry/spec/api/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ['it', 'packages']  # optional
paging = True

base_url = "https://hub.docker.com"
page_size = 10


def request(query, params):
    args = {
        "query": query,
        "from": page_size * (params['pageno'] - 1),
        "size": page_size,
    }
    params['url'] = f"{base_url}/api/search/v3/catalog/search?{urlencode(args)}"

    return params


def response(resp):
    '''post-response callback
    resp: requests response object
    '''
    results = []
    json_resp = resp.json()

    for item in json_resp.get("results", []):
        image_source = item.get("source")
        is_official = image_source in ["store", "official"]

        popularity_infos = [f"{item.get('star_count', 0)} stars"]

        architectures = []
        for rate_plan in item.get("rate_plans", []):
            pull_count = rate_plan.get("repositories", [{}])[0].get("pull_count")
            if pull_count:
                popularity_infos.insert(0, f"{pull_count} pulls")
            architectures.extend(arch['name'] for arch in rate_plan.get("architectures", []) if arch['name'])

        result = {
            'template': 'packages.html',
            'url': base_url + ("/_/" if is_official else "/r/") + item.get("slug", ""),
            'title': item.get("name"),
            'content': item.get("short_description"),
            'thumbnail': item["logo_url"].get("large") or item["logo_url"].get("small"),
            'package_name': item.get("name"),
            'maintainer': item["publisher"].get("name"),
            'publishedDate': parser.parse(item.get("updated_at") or item.get("created_at")),
            'popularity': ', '.join(popularity_infos),
            'tags': architectures,
        }
        results.append(result)

    return results
