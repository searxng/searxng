# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cargo search on crates.io"""

from collections import OrderedDict
from urllib.parse import urlencode

from dateutil import parser

about = {
    "website": "https://crates.io/",
    "wikidata_id": None,
    "official_api_documentation": "https://crates.io/data-access",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

categories = ["it", "packages", "cargo"]


# engine dependent config
paging = True
page_size = 10
search_url = "https://crates.io/api/v1/crates"

linked_terms = OrderedDict(
    [
        ("homepage", "Project homepage"),
        ("documentation", "Documentation"),
        ("repository", "Source code"),
    ]
)


def request(query: str, params):

    args = urlencode({"page": params["pageno"], "q": query, "per_page": page_size})
    params["url"] = f"{search_url}?{args}"
    return params


def response(resp):
    results = []

    for package in resp.json()["crates"]:

        published_date = package.get("updated_at")
        published_date = parser.parse(published_date)

        links = {}
        for k, v in linked_terms.items():
            l = package.get(k)
            if l:
                links[v] = l

        results.append(
            {
                "template": "packages.html",
                "url": f'https://crates.io/crates/{package["name"]}',
                "title": package["name"],
                "package_name": package["name"],
                "tags": package["keywords"],
                "content": package["description"],
                "version": package["newest_version"] or package["max_version"] or package["max_stable_version"],
                "publishedDate": published_date,
                "links": links,
            }
        )

    return results
