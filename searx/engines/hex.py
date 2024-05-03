# SPDX-License-Identifier: AGPL-3.0-or-later
"""hex.pm"""

from urllib.parse import urlencode
from dateutil import parser


about = {
    # pylint: disable=line-too-long
    "website": "https://hex.pm/",
    "wikidata_id": None,
    "official_api_documentation": "https://github.com/hexpm/hexpm/blob/main/lib/hexpm_web/controllers/api/package_controller.ex",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

categories = ["it", "packages"]


# engine dependent config
paging = True
search_url = "https://hex.pm/api/packages/"


def request(query: str, params):
    args = urlencode({"page": params["pageno"], "search": query})
    params["url"] = f"{search_url}?{args}"
    return params


def response(resp):
    results = []
    for package in resp.json():
        meta = package["meta"]
        publishedDate = package.get("inserted_at")
        if publishedDate:
            publishedDate = parser.parse(publishedDate)
        tags = meta.get("licenses", [])
        results.append(
            {
                "template": "packages.html",
                "url": package["url"],
                "title": package["name"],
                "package_name": package["name"],
                "content": meta.get("description", ""),
                "version": meta.get("latest_version"),
                "maintainer": ", ".join(meta.get("maintainers", [])),
                "publishedDate": publishedDate,
                "tags": tags,
                "homepage": meta.get("links", {}).get("homepage"),
                "source_code_url": meta.get("links", {}).get("github"),
            }
        )

    return results
