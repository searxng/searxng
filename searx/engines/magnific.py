# SPDX-License-Identifier: AGPL-3.0-or-later
"""Magnific_ is a database for images.

.. _Magnific: https://www.magnific.com
"""

import re
from urllib.parse import urlencode

import typing as t

from searx.enginelib import EngineCache
from searx.exceptions import SearxEngineAPIException
from searx.network import get, post
from searx.result_types import EngineResults
from searx.utils import eval_xpath_getindex, extract_text

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://www.magnific.com",
    "wikidata_id": "Q104211654",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

base_url = "https://www.magnific.com"

categories = ["stock images"]
paging = True

free_images_only = True
"""
Whether to only load images that may be used for free, without a Magnific account.
"""

# regular expressions for solving the captcha
_NUMBER_RE = re.compile(r"\d+")
_BM_VERIFY_RE = re.compile(r"\"bm-verify\":\s*\"(.*?)\"")
_CAPTCHA_COOKIE_NAME = "ak_bmsc"

CACHE: EngineCache
"""Cache for storing the cookie to bypass botblocking, obtained by solving a CAPTCHA."""


def setup(engine_settings: dict[str, t.Any]):
    global CACHE  # pylint: disable=global-statement
    CACHE = EngineCache(engine_settings["name"])


def _solve_captcha(original_resp: "SXNG_Response") -> "SXNG_Response":
    """Solves the Magnific CAPTCHA by summing all numbers in the response.
    E.g., the relevant part of the script that contains the numbers could look like
    ``var i = 1789729970; var j = i + Number("1947" + "43160");``."""
    doc = original_resp.html()
    script = extract_text(eval_xpath_getindex(doc, "//script", 0)) or ""

    bm_verify = _BM_VERIFY_RE.search(original_resp.text)
    if not bm_verify:
        raise SearxEngineAPIException("failed to extract bm verify token")
    bm_verify = bm_verify.group(1)

    # challenge is just adding a bunch of number together (some are strings, some are ints)
    numbers = [int(m) for m in _NUMBER_RE.findall(script)]
    solution = sum(numbers)

    challenge_resp = post(
        f"{base_url}/_sec/verify?provider=interstitial",
        json={"bm-verify": bm_verify, "pow": solution},
        cookies=original_resp.cookies,
    )

    resp = get(original_resp.url, headers=original_resp.search_params["headers"], cookies=challenge_resp.cookies)
    # cookie is valid for 2 hours
    CACHE.set(_CAPTCHA_COOKIE_NAME, challenge_resp.cookies[_CAPTCHA_COOKIE_NAME], expire=7200)
    return resp


def request(query: str, params: "OnlineParams") -> None:
    args = {"term": query, "filters[ai-generated][excluded]": 1, "page": params["pageno"], "locale": "en"}
    if free_images_only:
        args["filters[license]"] = "free"

    params["headers"]["Referer"] = f"{base_url}/search"

    # cookie that is obtained after solving the CAPTCHA
    if cookie := CACHE.get(_CAPTCHA_COOKIE_NAME):
        params["cookies"][_CAPTCHA_COOKIE_NAME] = cookie

    params["url"] = f"{base_url}/api/regular/search?{urlencode(args)}"


def response(resp: "SXNG_Response"):
    if resp.headers["content-type"] == "text/html":
        resp = _solve_captcha(resp)

    res = EngineResults()

    result: dict[str, t.Any]  # TBH: dict[str, t.Any]
    for result in resp.json()["items"]:
        res.add(
            res.types.Image(
                title=result["name"],
                url=result["url"],
                thumbnail_src=result["preview"]["url"],
                img_src=result["preview"]["url"],
                resolution=f"{result['preview']['width']}x{result['preview']['height']}",
            )
        )

    return res
