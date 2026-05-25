# SPDX-License-Identifier: AGPL-3.0-or-later
"""MyMemory Translated"""

import typing as t

import urllib.parse

from searx.utils import html_to_text
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineDictParams
#
# about
about = {
    "website": "https://mymemory.translated.net/",
    "wikidata_id": None,
    "official_api_documentation": "https://mymemory.translated.net/doc/spec.php",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

engine_type = "online_dictionary"
categories = ["general", "translate"]
api_url = "https://api.mymemory.translated.net"
web_url = "https://mymemory.translated.net"
weight = 100

api_key = ""


def request(_: str, params: "OnlineDictParams") -> None:

    args = {
        "q": params["query"],
        "langpair": f"{params['from_lang'][1]}|{params['to_lang'][1]}",
    }
    if api_key:
        args["key"] = api_key

    params['url'] = f"{api_url}/get?{urllib.parse.urlencode(args)}"


def response(resp: "SXNG_Response") -> EngineResults:

    results = EngineResults()
    data: dict[str, t.Any] = resp.json()
    params: "OnlineDictParams" = resp.search_params  # pyright: ignore[reportAssignmentType]

    args = {
        "q": params["query"],
        "lang": params.get("searxng_locale", "en"),  # ui language
        "sl": params["from_lang"][1],
        "tl": params["to_lang"][1],
    }

    link = f"{web_url}/search.php?{urllib.parse.urlencode(args)}"
    text: str = html_to_text(data["responseData"]["translatedText"])

    examples: set[str] = set()
    match: dict[str, str]
    for match in data["matches"]:
        _text = html_to_text(match["translation"])
        if _text != text:
            _seg = html_to_text(match["segment"])
            examples.add(f"{_seg} : {_text}")

    item = results.types.Translations.Item(text=text, examples=list(examples))
    results.add(results.types.Translations(translations=[item], url=link))

    return results
