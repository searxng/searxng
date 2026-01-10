# SPDX-License-Identifier: AGPL-3.0-or-later
"""CachyOS (packages, it)"""

from urllib.parse import urlencode
from datetime import datetime
from searx.result_types import EngineResults

about = {
    "website": 'https://cachyos.org',
    "wikidata_id": "Q116777127",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

base_url = "https://packages.cachyos.org/api/search"
categories = ['packages', 'it']
paging = True
results_per_page = 15


def request(query, params):
    query_params = {
        "search": query,
        "page_size": results_per_page,
        "current_page": params["pageno"],
    }

    params["url"] = f"{base_url}?{urlencode(query_params)}"

    return params


def response(resp) -> EngineResults:
    results = EngineResults()
    search_res = resp.json()

    for item in search_res["packages"]:
        package_name = item["pkg_name"]
        arch = item["pkg_arch"]
        repo = item["repo_name"]

        results.add(
            results.types.LegacyResult(
                {
                    "template": 'packages.html',
                    "url": f"https://packages.cachyos.org/package/{repo}/{arch}/{package_name}",
                    "title": f"{package_name} ({repo})",
                    "package_name": package_name,
                    "publishedDate": datetime.fromtimestamp(item["pkg_builddate"]),
                    "version": item["pkg_version"],
                    "content": item["pkg_desc"],
                    "tags": [arch],
                }
            )
        )

    return results
