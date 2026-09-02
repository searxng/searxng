# SPDX-License-Identifier: AGPL-3.0-or-later
"""SearchZee is a small, indie project, web and news results pulled from
independent search infrastructure."""

import typing as t
from urllib.parse import urlencode
import uuid

from searx.extended_types import SXNG_Response
from searx.result_types import EngineResults
from searx.utils import html_to_text

if t.TYPE_CHECKING:
    from searx.search.processors import OnlineParams

about = {
    "website": "https://searchzee.com",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
    "description": (
        "SearchZee is a small, indie project, the web and news results"
        " are pulled from an independent search infrastructure."
    ),
}
categories: list[str] = None  # type: ignore[reportAssignmentType]

paging = True

SearchzeeCategType = t.Literal["web", "news"]
searchzee_categ: SearchzeeCategType = None  # type: ignore[reportAssignmentType]


base_url = "https://searchzee.com"

# only supports for news
time_range_map = {"day": "pd", "week": "pw", "month": "pm", "year": "py"}


def setup(_: dict[str, t.Any]):
    if searchzee_categ not in t.get_args(SearchzeeCategType):
        raise ValueError("invalid category: %s" % searchzee_categ)


def request(query: str, params: "OnlineParams"):
    params["cookies"]["szs"] = str(uuid.uuid4())

    args = {"q": query, "type": searchzee_categ, "offset": params["pageno"] - 1}
    if params["time_range"]:
        args["freshness"] = time_range_map[params["time_range"]]
    params["url"] = f"{base_url}/api/search?{urlencode(args)}"


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()

    results: list[dict[str, str]] = resp.json()["results"]  # type: ignore[reportAny]

    for result in results:
        res.add(
            res.types.MainResult(
                url=result["url"],
                title=html_to_text(result["title"]),
                content=html_to_text(result["summary"]),
                thumbnail=result.get("thumbnail") or "",
            )
        )

    return res
