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

base_url = "https://hub.docker.com/"
search_url = base_url + "api/content/v1/products/search?{query}&type=image&page_size=25"


def request(query, params):

    params['url'] = search_url.format(query=urlencode(dict(q=query, page=params["pageno"])))
    params["headers"]["Search-Version"] = "v3"

    return params


def response(resp):
    '''post-response callback
    resp: requests response object
    '''
    results = []
    body = resp.json()

    for item in body.get("summaries", []):
        filter_type = item.get("filter_type")
        is_official = filter_type in ["store", "official"]

        result = {
            'template': 'packages.html',
            'url': base_url + ("_/" if is_official else "r/") + item.get("slug", ""),
            'title': item.get("name"),
            'content': item.get("short_description"),
            'img_src': item["logo_url"].get("large") or item["logo_url"].get("small"),
            'package_name': item.get("name"),
            'maintainer': item["publisher"].get("name"),
            'publishedDate': parser.parse(item.get("updated_at") or item.get("created_at")),
            'popularity': item.get("pull_count", "0") + " pulls",
            'tags': [arch['name'] for arch in item["architectures"]],
        }
        results.append(result)

    return results
