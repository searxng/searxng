# SPDX-License-Identifier: AGPL-3.0-or-later
"""Andisearch (general)"""

from datetime import datetime
import json
import typing as t

from searx.exceptions import SearxEngineAPIException
from searx.extended_types import SXNG_Response
from searx.network import get
from searx.result_types import EngineResults
from searx.utils import html_to_text
from searx.enginelib import EngineCache

if t.TYPE_CHECKING:
    from searx.search.processors import OnlineParams

about = {
    "website": "https://andisearch.com",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}
categories = ["general"]

CACHE: EngineCache
"""Cache for storing the API Token."""

base_url = "https://andisearch.com"

AndisearchCategory = t.Literal["results", "news", "images"]
andisearch_categ: AndisearchCategory = "results"


def setup(_: dict[str, t.Any]):
    if andisearch_categ not in t.get_args(AndisearchCategory):
        raise ValueError(f"invalid andisearch category: {andisearch_categ!r}")

    global CACHE  # pylint: disable=global-statement
    CACHE = EngineCache("andisearch")


def _obtain_api_token() -> str:
    token: str
    if token := CACHE.get("token"):
        return token

    # user agent for token request must be the same as for the main request
    token_resp = get(f"{base_url}/api/token", headers={"Referer": f"{base_url}/"}, impersonate="firefox")
    if not token_resp.ok:
        raise SearxEngineAPIException("failed to obtain api key")

    token = token_resp.json()["token"]
    CACHE.set("token", token, expire=5 * 60)

    return token


def request(query: str, params: "OnlineParams"):
    params["url"] = f"{base_url}/api/search"
    params["headers"]["x-api-token"] = _obtain_api_token()
    params["headers"]["Origin"] = f"{base_url}"
    params["headers"]["Referer"] = f"{base_url}/"
    params["impersonate"] = "firefox"

    params["method"] = "POST"
    params["json"] = {
        "inputTranscript": query,
        "requestAttributes": {
            "compress": "false",
            "features": "deep answers",
            "persona": "mixed",
            "safety": "false",
            "cleanup": "true",
            "maxPayloadSize": "200000",
        },
        "sessionAttributes": {"format": "json"},
    }


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()

    results_json = resp.json()["sessionState"]["sessionAttributes"]["currentSearchResult"]
    parsed = json.loads(results_json)

    if answer := parsed.get("answer"):
        res.add(res.types.Answer(answer=html_to_text(answer), url=parsed.get("link")))

    results: list[dict[str, str]] = parsed[andisearch_categ]  # type: ignore[reportAny]
    for result in results:
        if andisearch_categ in ("results", "news"):
            publishedDate = None
            if result.get("date"):
                publishedDate = datetime.fromisoformat(result["date"])

            res.add(
                res.types.MainResult(
                    url=result["link"],
                    title=html_to_text(result["title"]),
                    content=html_to_text(result["desc"]),
                    thumbnail=result.get("image") or "",
                    publishedDate=publishedDate,
                )
            )
        elif andisearch_categ == "images":
            resolution = ""
            if result.get("width") and result.get("height"):
                resolution = f"{result['width']}x{result['height']}"
            res.add(
                res.types.Image(
                    url=result["link"], title=result["title"], img_src=result["image"], resolution=resolution
                )
            )

    return res
