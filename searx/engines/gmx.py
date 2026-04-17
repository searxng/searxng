# SPDX-License-Identifier: AGPL-3.0-or-later
"""GMX (general)

It's unclear which index it uses, the results were the most similar to Google's.

In theory it supports multiple languages, but even if changing the region on their website,
most of the results are still in English."""

import time
import typing as t

from urllib.parse import urlencode

from searx.result_types import EngineResults
from searx.extended_types import SXNG_Response
from searx.utils import extr, gen_useragent, html_to_text
from searx.network import get

if t.TYPE_CHECKING:
    from searx.search.processors import OnlineParams

about = {
    "website": "https://search.gmx.com",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

base_url = "https://search.gmx.com"  # alternatively: search.gmx.net
categories = ["general"]

paging = True
safesearch = True
time_range_support = True

time_range_map = {"day": "d", "week": "w", "month": "m", "year": "y"}


def _get_page_hash(query: str, page: int, headers: dict[str, str]) -> str:
    resp = get(f"{base_url}/web/result?q={query}&page={page}", headers=headers)

    # the text we search for looks like:
    # load("/desk?lang="+eV.p.param['hl']+"&q="+eV['p']['q_encode']+"&page=5&h=aa45603&t=177582576&origin=web&comp=web_serp_pag&p=gmx-com&sp=&lr="+eV.p.param['lr0']+"&mkt="+eV.p.param['mkt0']+"&family="+eV.p.param['familyFilter']+"&fcons="+eV.p.perm.fCons,"google", "eMMO", "eMH","eMP");  # pylint: disable=line-too-long
    return extr(resp.text, "&h=", "&t=")


def request(query: str, params: 'OnlineParams'):
    # the headers have to be as close to normal browsers as possible, otherwise you get rate-limited quickly
    # the user agent for loading the hash and requesting the results has to be the same
    headers = {
        "User-Agent": gen_useragent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Referer": base_url,
    }

    # the "h" parameter has to be set to the current time in seconds with the last digit removed
    # e.g., if the current time is 1775829848, h has to be 177582984
    now = int(time.time() / 10)

    # the page hash depends on the query and page number
    page_hash = _get_page_hash(query, params["pageno"], headers)
    # the headers have to match the ones from the previous request

    args = {"lang": "en", "q": query, "page": params["pageno"], "h": page_hash, "t": now}
    if params["safesearch"]:
        args["family"] = True
    if params.get("time_range"):
        args["time"] = time_range_map[params["time_range"]]

    params["url"] = f"{base_url}/desk?{urlencode(args)}"

    params["headers"].update(headers)


def response(resp: 'SXNG_Response') -> EngineResults:
    res = EngineResults()

    results = resp.json()["results"]

    for suggestion in results["rs"]:
        res.add(res.types.LegacyResult({"suggestion": suggestion["t"]}))

    for result in results["hits"]:
        res.add(
            res.types.MainResult(
                url=result["u"],
                title=html_to_text(result["t"]),
                content=html_to_text(result["s"]),
            )
        )

    return res
