# SPDX-License-Identifier: AGPL-3.0-or-later
"""Neosearch_ aims to be a privacy-first alternative to Google.

.. _Neosearch: https://neosearch.org/About
"""

from json import loads
import typing as t
from urllib.parse import urlencode

from searx.extended_types import SXNG_Response
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.enginelib.traits import EngineTraits
    from searx.search.processors import OnlineParams

    traits: EngineTraits

about = {
    "website": "https://neosearch.org",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

base_url = "https://neosearch.org"
categories = ["general"]

paging = False


def request(query: str, params: "OnlineParams"):
    args = {"q": query, "generate": "auto"}
    countrycode = params["searxng_locale"].split("-")[-1].upper()
    if countrycode in traits.custom["countrycodes"]:
        args["loc"] = countrycode
    params["url"] = f"{base_url}/search?{urlencode(args)}"


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()

    # first line contains something like `{"location": "de"}`
    # second line contains the actual results
    json_resp = loads(resp.text.splitlines()[-1])
    for lens in json_resp["lenses"]:
        for category in lens["categories"]:
            for result in category["links"]:
                if not result["url"]:
                    continue

                res.add(
                    res.types.MainResult(
                        url=result["url"],
                        title=result["title"],
                        content=result["snippet"] or result["description"],
                    )
                )

    for suggestion in json_resp.get("suggestions", []):
        res.add(res.types.LegacyResult(suggestion=suggestion))

    return res


def fetch_traits(engine_traits: "EngineTraits") -> None:
    # pylint: disable=import-outside-toplevel
    from searx.network import get
    from searx.utils import extr, js_obj_str_to_python
    from babel.core import get_global

    resp = get(base_url)

    locations_js_raw = extr(resp.text, "const LOCATIONS = ", ";")
    if not locations_js_raw:
        raise RuntimeError("failed to find locations in neosearch HTML response")
    locations: list[dict[str, str]] = js_obj_str_to_python(locations_js_raw)

    babel_reg_list = get_global("territory_languages").keys()

    countrycodes: list[str] = []
    for loc in locations:
        _reg = loc["code"].upper()
        if _reg not in babel_reg_list:
            print(f"ERROR: region tag {_reg} is unknown by babel")
            continue
        countrycodes.append(_reg)

    countrycodes.sort()
    engine_traits.custom["countrycodes"] = countrycodes
