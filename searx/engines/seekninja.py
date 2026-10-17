# SPDX-License-Identifier: AGPL-3.0-or-later
"""Seek ninja (general)"""

from json import loads
from hashlib import sha256
from urllib.parse import urlencode, quote_plus

import typing as t

from searx.extended_types import SXNG_Response
from searx.network import get
from searx.result_types import EngineResults
from searx.utils import extr, html_to_text

if t.TYPE_CHECKING:
    from searx.search.processors import OnlineParams

about = {
    "website": "https://seek.ninja",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

safesearch = True

base_url = "https://seek.ninja"
categories = ["general"]

safe_search_map = {0: "off", 1: "moderate", 2: "strict"}

PowChallenge = dict[str, t.Any]


def _get_challenge(query: str) -> PowChallenge:
    """Extract the challenge parameters (i.e. nonce, difficulty, ...) from the
    search website."""

    resp = get(f"{base_url}/s?q={quote_plus(query)}")
    challenge_raw_json = "{" + extr(resp.text, "pow: {", "},") + "}"
    return loads(challenge_raw_json)


def _solve_pow(challenge: PowChallenge) -> list[int]:
    """Solves a Proof of Work SHA256 challenges. This is a 1:1 port of the
    site's JS code.

    On a high-level, it tries to ``k`` amount of solutions, where its sha256
    hash begins with: ``leading`` 0s, i.e.

    .. code: js

       sha256(nonce || solution).startswith("0" * leading)
    """
    nonce = challenge["nonce"]
    k = int(challenge["k"])
    indifficulty = float(challenge["indifficulty"])

    leading = int(indifficulty)
    frac = indifficulty - leading
    prefix = "".join("0" for _ in range(0, leading))

    maxNib = 15 - int(frac * 16) if frac else 15

    solutions: list[int] = []
    ans = 0
    while len(solutions) < k:
        h = sha256(f"{nonce}{ans}".encode()).hexdigest()
        if h.startswith(prefix) and (not frac or int(h[leading], base=16) <= maxNib):
            solutions.append(ans)
        ans += 1
    return solutions


def request(query: str, params: 'OnlineParams') -> None:
    challenge = _get_challenge(query)
    solution = _solve_pow(challenge)
    args = {
        "q": query,
        "panswers": ",".join(str(s) for s in solution),
        "pid": challenge["challengeId"],
        "adult": safe_search_map[params["safesearch"]],
    }
    params["url"] = f"{base_url}/search-sse?{urlencode(args)}"


def response(resp: 'SXNG_Response') -> EngineResults:
    res = EngineResults()
    # The response is a stream of server-side events,
    # so it is split into `event: <type>` and `data: {"results": ...}`
    # see https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/
    events = resp.text.split("\n\n")
    for event in events:
        event_parts = event.split("\n", maxsplit=2)
        if len(event_parts) != 2:
            continue

        event_name, data = event_parts
        if not event_name.endswith("resultsUpdate"):
            continue

        json_data = loads(data.removeprefix("data: "))
        for result in json_data["results"]:
            res.add(
                res.types.MainResult(
                    url=result["url"],
                    title=result["title"],
                    content=html_to_text(result["blurb"]),
                )
            )

    return res
