# SPDX-License-Identifier: AGPL-3.0-or-later
"""JavaScript-based s1search implementation. See :ref:`s1search engine`.

Works for all s1search sites that contain the ``__RAMPJS__`` JavaScript variable.
"""

import json
import typing as t
from urllib.parse import urlencode

from searx.result_types import EngineResults
from searx.utils import extr, html_to_text

if t.TYPE_CHECKING:
    from searx.search.processors import OnlineParams
    from searx.extended_types import SXNG_Response

about = {
    "website": "https://s1search.co",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

categories = ["general"]
paging = True

base_url = "https://search.answers.com"
# other working base URLs:
# - https://search.nation.online
# - https://search.activebeat.com
# - https://search.legalboulevard.com
# - https://search.walletgenius.com
# - https://search.legalboulevard.com


def request(query: str, params: "OnlineParams"):
    args = {"q": query, "page": params["pageno"]}
    params["url"] = f"{base_url}/?{urlencode(args)}"


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()

    data_raw = extr(resp.text, "response: ", " };")
    data = json.loads(data_raw)

    mainline = [s for s in data["search"]["regions"] if s["name"] == "mainline"][0]
    for group in mainline["groups"]:
        for result in group["results"]:
            if not ("url" in result or "clickUrl" in result):
                continue

            res.add(
                res.types.MainResult(
                    url=result.get("url") or result.get("clickUrl"),
                    title=html_to_text(result["title"]),
                    content=html_to_text(result["description"]),
                )
            )

    return res
