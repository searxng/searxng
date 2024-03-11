# SPDX-License-Identifier: AGPL-3.0-or-later
"""npms.io

"""

from urllib.parse import urlencode
from dateutil import parser


about = {
    "website": "https://npms.io/",
    "wikidata_id": "Q7067518",
    "official_api_documentation": "https://api-docs.npms.io/",
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

categories = ['it', 'packages']


# engine dependent config
paging = True
page_size = 25
search_api = "https://api.npms.io/v2/search?"


def request(query: str, params):

    args = urlencode(
        {
            'from': (params["pageno"] - 1) * page_size,
            'q': query,
            'size': page_size,
        }
    )
    params['url'] = search_api + args
    return params


def response(resp):
    results = []
    content = resp.json()
    for entry in content["results"]:
        package = entry["package"]
        publishedDate = package.get("date")
        if publishedDate:
            publishedDate = parser.parse(publishedDate)
        tags = list(entry.get("flags", {}).keys()) + package.get("keywords", [])
        results.append(
            {
                "template": "packages.html",
                "url": package["links"]["npm"],
                "title": package["name"],
                'package_name': package["name"],
                "content": package.get("description", ""),
                "version": package.get("version"),
                "maintainer": package.get("author", {}).get("name"),
                'publishedDate': publishedDate,
                "tags": tags,
                "homepage": package["links"].get("homepage"),
                "source_code_url": package["links"].get("repository"),
            }
        )

    return results
