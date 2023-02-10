# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Docker Hub (IT)

"""
# pylint: disable=use-dict-literal

from json import loads
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

categories = ['it']  # optional
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
    body = loads(resp.text)

    # Make sure `summaries` isn't `null`
    search_res = body.get("summaries")
    if search_res:
        for item in search_res:
            result = {}

            # Make sure correct URL is set
            filter_type = item.get("filter_type")
            is_official = filter_type in ["store", "official"]

            if is_official:
                result["url"] = base_url + "_/" + item.get('slug', "")
            else:
                result["url"] = base_url + "r/" + item.get('slug', "")
            result["title"] = item.get("name")
            result["content"] = item.get("short_description")
            result["publishedDate"] = parser.parse(item.get("updated_at") or item.get("created_at"))
            result["thumbnail"] = item["logo_url"].get("large") or item["logo_url"].get("small")
            results.append(result)

    return results
