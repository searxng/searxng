# SPDX-License-Identifier: AGPL-3.0-or-later
"""Currency convert (DuckDuckGo)"""

import typing as t
import json
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.search.processors import OnlineCurrenciesParams
    from searx.extended_types import SXNG_Response

# about
about = {
    "website": "https://duckduckgo.com/",
    "wikidata_id": "Q12805",
    "official_api_documentation": "https://duckduckgo.com/api",
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSONP",
    "description": "Service from DuckDuckGo.",
}

engine_type = "online_currency"
categories = ["currency", "general"]

base_url = "https://duckduckgo.com/js/spice/currency/1/%(from_iso4217)s/%(to_iso4217)s"
ddg_link_url = "https://duckduckgo.com/?q=%(from_iso4217)s+to+%(to_iso4217)s"

weight = 100


def request(query: str, params: "OnlineCurrenciesParams") -> None:  # pylint: disable=unused-argument
    params["url"] = base_url % params


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()

    # remove first and last lines to get only json
    json_resp = resp.text[resp.text.find("\n") + 1 : resp.text.rfind("\n") - 2]
    try:
        conversion_rate = float(json.loads(json_resp)["to"][0]["mid"])
    except IndexError:
        return res

    params: OnlineCurrenciesParams = resp.search_params  # pyright: ignore[reportAssignmentType]
    answer = "{0} {1} = {2} {3} (1 {5} : {4} {6})".format(
        params["amount"],
        params["from_iso4217"],
        params["amount"] * conversion_rate,
        params["to_iso4217"],
        conversion_rate,
        params["from_name"],
        params["to_name"],
    )
    url = ddg_link_url % params
    res.add(res.types.Answer(answer=answer, url=url))
    return res
