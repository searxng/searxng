# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exa is a web search built for AI agents."""

import typing as t

from searx.exceptions import SearxEngineAPIException
from searx.extended_types import SXNG_Response
from searx.network import post
from searx.result_types import EngineResults
from searx.enginelib import EngineCache

if t.TYPE_CHECKING:
    from searx.search.processors import OnlineParams

about = {
    "website": "https://exa.ai",
    "official_api_documentation": "https://exa.ai/docs/reference/search-api-guide",
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}
categories = ["general"]

page_size = 10
"""Page size must be less or equal than 10."""

exa_mode: t.Literal["fast", "auto", "instant", "deep", "deep-lite", "deep-reasoning"] = "auto"
"""Search type. See the `documentation <https://exa.ai/docs/reference/search#body-type-one-of-0>`_."""

CACHE: EngineCache
"""Cache for storing the scraped API Token."""

base_url = "https://exa.ai"


def setup(engine_settings: dict[str, t.Any]) -> bool:
    global CACHE  # pylint: disable=global-statement
    CACHE = EngineCache(engine_settings["name"])  # type: ignore[reportAny]
    return True


def _obtain_api_token() -> str:
    token: str | None = CACHE.get("token")  # type: ignore[reportAny]
    if token:
        return token

    token_resp = post(
        f"{base_url}/api/token/issue",
    )
    if not token_resp.ok:
        raise SearxEngineAPIException("failed to obtain api key")

    resp_json = token_resp.json()
    token = resp_json["token"]
    if not token:
        raise SearxEngineAPIException("failed to obtain api key")

    # we subtract a few seconds from the expiry time to make sure there's no
    # state where we use the old, invalid token although it's no longer valid
    expire = resp_json["expiresIn"] - 5
    CACHE.set("token", token, expire=expire)

    return token


def request(query: str, params: "OnlineParams"):
    body = {
        "query": query,
        "type": exa_mode,
        "num_results": page_size,
        "contents": {"text": {"maxCharacters": 500, "stripLinks": True}},
        "outputSchema": {"type": "text"},
    }
    params["headers"]["Authorization"] = f"Bearer {_obtain_api_token()}"

    params["url"] = f"{base_url}/api/search"
    params["method"] = "POST"
    params["json"] = body


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()

    results: list[dict[str, str]] = resp.json()["results"]  # type: ignore[reportAny]

    for result in results:
        res.add(
            res.types.MainResult(
                url=result["url"],
                title=result["title"],
                content=result["text"],
                thumbnail=result.get("image") or "",
            )
        )

    return res
