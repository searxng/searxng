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
# Valid values: name inserted_at updated_at total_downloads recent_downloads
sort_criteria = "recent_downloads"
page_size = 10

linked_terms = {
    # lower-case : replacement
    "author": "Author",
    "bitbucket": "Bitbucket",
    "bug tracker": "Issue tracker",
    "changelog": "Changelog",
    "doc": "Documentation",
    "docs": "Documentation",
    "documentation": "Documentation",
    "github repository": "GitHub",
    "github": "GitHub",
    "gitlab": "GitLab",
    "issues": "Issue tracker",
    "project source code": "Source code",
    "repository": "Source code",
    "scm": "Source code",
    "sourcehut": "SourceHut",
    "sources": "Source code",
    "sponsor": "Sponsors",
    "sponsors": "Sponsors",
    "website": "Homepage",
}


def request(query: str, params):
    args = urlencode({"page": params["pageno"], "per_page": page_size, "sort": sort_criteria, "search": query})
    params["url"] = f"{search_url}?{args}"
    return params


def response(resp):
    results = []
    for package in resp.json():
        meta = package["meta"]
        published_date = package.get("updated_at")
        published_date = parser.parse(published_date)
        links = {linked_terms.get(k.lower(), k): v for k, v in meta.get("links").items()}
        results.append(
            {
                "template": "packages.html",
                "url": package["html_url"],
                "title": package["name"],
                "package_name": package["name"],
                "content": meta.get("description", ""),
                "version": meta.get("latest_version"),
                "maintainer": ", ".join(meta.get("maintainers", [])),
                "publishedDate": published_date,
                "license_name": ", ".join(meta.get("licenses", [])),
                "homepage": package["docs_html_url"],
                "links": links,
            }
        )

    return results
