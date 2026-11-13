# SPDX-License-Identifier: AGPL-3.0-or-later
"""NuGet Gallery on nuget.org"""

import typing as t
from urllib.parse import urlencode

from searx.enginelib import EngineCache
from searx.extended_types import SXNG_Response
from searx.network import get
from searx.result_types import EngineResults
from searx.search.processors import OnlineParams

about = {
    "website": "https://nuget.org/",
    "wikidata_id": None,
    "official_api_documentation": "https://learn.microsoft.com/en-us/nuget/api/overview",
    "use_official_api": True,
    "require_api_key": False,
    "description": (
        "NuGet is the package manager for .NET. "
        "The NuGet client tools provide the ability to produce and consume packages. "
        "The NuGet Gallery is the central package repository used by all package authors and consumers."
    ),
}

# engine dependent config
engine_type = "online"
categories = ["it", "packages", "nuget"]
paging = True
page_size = 20
index_url = "https://api.nuget.org/v3/index.json"
web_base_url = "https://nuget.org/"
search_resource_type = "SearchQueryService"
CACHE: EngineCache


def init(engine_settings: dict[str, t.Any]):
    global CACHE  # pylint: disable=global-statement
    CACHE = EngineCache(engine_settings["name"])


def _get_search_url() -> str:
    if search_url := CACHE.get("nuget_search_url"):
        return search_url

    resp = get(index_url)
    resources: list[dict[str, str]] = resp.json()["resources"]
    search_resource = next(
        # will also select `SearchQueryService/3.0.0-rc` and `SearchQueryService/3.5.0`
        # 3.0.0-rc is just an alias, and 3.5.0 supports package type filtering, which doesn't matter here
        filter(
            lambda res: res["@type"].startswith(search_resource_type),
            resources,
        )
    )
    search_url = search_resource["@id"]

    return search_url


def request(query: str, params: OnlineParams) -> None:
    search_url = _get_search_url()
    args = urlencode({"q": query, "skip": (params["pageno"] - 1) * page_size, "take": page_size})
    params["url"] = f"{search_url}?{args}"


def response(resp: SXNG_Response):
    res = EngineResults()

    for package in resp.json()["data"]:
        res.append(
            res.types.LegacyResult(
                template="packages.html",
                url=f"{web_base_url}/packages/{package['id']}/{package['version']}",
                title=package["id"],
                package_name=package["id"],
                tags=package.get("tags"),
                content=package.get("description"),
                version=package["version"],
                homepage=package.get("projectUrl"),
            )
        )

    return res
