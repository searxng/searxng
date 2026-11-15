# SPDX-License-Identifier: AGPL-3.0-or-later
"""pkg.go.dev (packages)"""

import typing as t

from urllib.parse import urlencode

from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://pkg.go.dev/",
    "use_official_api": True,
    "official_api_documentation": "https://pkg.go.dev/v1/api",
    "require_api_key": False,
    "results": "JSON",
}

categories = ["packages", "it"]

base_url = "https://pkg.go.dev"


def request(query: str, params: "OnlineParams"):
    args = {
        "q": query,
    }
    params["url"] = f"{base_url}/v1/search?{urlencode(args)}"


def response(resp):
    res = EngineResults()

    for result in resp.json()["items"]:
        res.add(
            res.types.LegacyResult(
                template="packages.html",
                url=f"{base_url}/{result['packagePath']}",
                title=result["packagePath"],
                content=result["synopsis"],
                package_name=result["packagePath"],
                version=result["version"],
            )
        )

    return res
