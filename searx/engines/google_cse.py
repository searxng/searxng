# SPDX-License-Identifier: AGPL-3.0-or-later
"""Google Custom Search Engine"""

import datetime
import typing as t
from json import loads
from urllib.parse import urlencode

from searx.enginelib import EngineCache
from searx.exceptions import SearxEngineAPIException, SearxEngineTooManyRequestsException
from searx.network import get
from searx.result_types import EngineResults

from searx.engines.google import fetch_traits  # pylint: disable=unused-import
from searx.engines.google import filter_mapping, get_google_info

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://www.google.com",
    "wikidata_id": "Q2233943",
    "official_api_documentation": "https://developers.google.com/custom-search/docs/element",
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSONP",
    "description": "Platform for creating custom search engines based on Google Search.",
}

categories = ["general", "web"]
paging = True
max_page = 5
page_size = 20
time_range_support = True
language_support = True
safesearch = True

CX = "partner-pub-8993703457585266:4862972284"  # blackle.com

CACHE: EngineCache


def setup(engine_settings: dict[str, t.Any]) -> bool:
    global CACHE  # pylint: disable=global-statement
    CACHE = EngineCache(engine_settings["name"])
    return True


def _cse_token() -> dict[str, str]:
    token: dict[str, str] = CACHE.get(CX)
    if token:
        return token

    resp = get(f"https://www.google.com/cse/cse.js?cx={CX}", timeout=10)
    if not resp.ok:
        raise SearxEngineAPIException("failed to obtain cse token")

    end = resp.text.rfind("});")
    start = resp.text.rfind("({")
    opts: dict[str, str] = loads(resp.text[start + 1 : end + 1])

    cse_tok = opts.get("cse_token")
    if not cse_tok:
        raise SearxEngineAPIException("failed to obtain cse token")

    exp = opts.get("exp")
    token = {
        "cse_tok": cse_tok,
        "cselibv": opts.get("cselibVersion", ""),
        "exp": ",".join(exp) if exp else "",
    }
    CACHE.set(CX, token, expire=3600)
    return token


def _get_start_and_end_date_str(time_range: str) -> tuple[str, str]:
    time_range_map = {"day": 1, "week": 7, "month": 30, "year": 365}

    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=time_range_map[time_range])

    return start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")


def request(query: str, params: "OnlineParams") -> None:
    token = _cse_token()

    google_info = get_google_info(params, traits)
    info: dict[str, str] = google_info["params"]

    hl = info["hl"]
    if params.get("searxng_locale", "all") == "all" or "ZZ" in hl:
        hl = "en"

    args = {
        "rsz": "filtered_cse",
        "num": str(page_size),
        "hl": hl,
        "cselibv": token["cselibv"],
        "cx": CX,
        "q": query,
        "safe": filter_mapping[params["safesearch"]],
        "cse_tok": token["cse_tok"],
        "callback": "_",
        "rurl": "",
    }
    if params["time_range"]:
        start_date, end_date = _get_start_and_end_date_str(params["time_range"])
        args["sort"] = f"date:r:{start_date}:{end_date}"

    if info.get("lr"):
        args["lr"] = info["lr"]
    if info.get("cr"):
        args["cr"] = info["cr"]
    if google_info["country"] not in (None, "ZZ"):
        args["gl"] = google_info["country"]
    if token["exp"]:
        args["exp"] = token["exp"]

    start = (params["pageno"] - 1) * page_size
    if start:
        args["start"] = str(start)

    params["url"] = "https://cse.google.com/cse/element/v1?" + urlencode(args)
    params["cookies"] = google_info["cookies"]
    params["headers"].update(google_info["headers"])
    params["headers"]["Referer"] = "https://cse.google.com/"


def response(resp: "SXNG_Response") -> EngineResults:
    json_resp = resp.text[resp.text.find("{") : resp.text.rfind("}") + 1]
    data = loads(json_resp)

    # not the real types, but a sufficient approximation
    item: dict[str, str]
    error: dict[str, str | int]

    if error := data.get("error"):
        message = error.get("message", "unknown error")
        if error.get("code") == 429:
            raise SearxEngineTooManyRequestsException(message=f"google cse: {message}")
        raise SearxEngineAPIException(f"google cse: {message}")

    results = EngineResults()
    for item in data.get("results", []):
        url = item.get("unescapedUrl")
        if not url:
            continue
        results.add(
            results.types.MainResult(
                url=url,
                title=item.get("titleNoFormatting", ""),
                content=item.get("contentNoFormatting", ""),
                thumbnail=item.get("richSnippet", {}).get("cseThumbnail", {}).get("src", ""),  # type: ignore
            )
        )
    return results
