# SPDX-License-Identifier: AGPL-3.0-or-later
"""Boardreader (forum search)"""

import re

from datetime import datetime
from urllib.parse import urlencode
import typing as t
import gettext
import babel

from searx.locales import language_tag
from searx.enginelib import EngineCache
from searx.enginelib.traits import EngineTraits
from searx.engines.json_engine import safe_search_map
from searx.exceptions import SearxEngineAPIException
from searx.network import get, raise_for_httperror
from searx.result_types import EngineResults
from searx.utils import extr, js_obj_str_to_python, html_to_text

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://boardreader.com",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

categories = ["general", "social media"]
paging = True
time_range_support = True

base_url = "https://boardreader.com"
time_range_map = {"day": "1", "week": "7", "month": "30", "year": "365"}

CACHE: EngineCache
CACHE_SESSION_ID_KEY = "session_id_key"

KEYWORD_RE = re.compile(r"\[\/?Keyword\]")


def init(engine_settings: dict[str, t.Any]) -> bool:
    global CACHE  # pylint: disable=global-statement
    CACHE = EngineCache(engine_name=engine_settings["name"])
    return True


def _get_session_id() -> str:
    cached: str | None = CACHE.get(CACHE_SESSION_ID_KEY)
    if cached:
        return cached

    resp = get(base_url)
    if resp.status_code != 200:
        raise_for_httperror(resp)

    session_id = extr(resp.text, "'currentSessionId', '", "'")
    if not session_id:
        raise SearxEngineAPIException("failed to obtain session id")

    CACHE.set(CACHE_SESSION_ID_KEY, session_id)
    return session_id


def request(query: str, params: "OnlineParams"):
    session_id = _get_session_id()

    language: str = traits.get_language(
        params["searxng_locale"], default="All"
    )  # pyright: ignore[reportAssignmentType]
    args = {
        "query": query,
        "page": params["pageno"],
        "language": language,
        "session_id": session_id,
    }
    if params["time_range"]:
        args["period"] = safe_search_map[params["time_range"]]  # pyright: ignore[reportArgumentType]

    params["url"] = f"{base_url}/return.php?{urlencode(args)}"
    return params


def _remove_keyword_marker(text: str) -> str:
    """
    Convert text like "[Keyword]ABCDE[/Keyword]" to "ABCDE".
    """
    return html_to_text(KEYWORD_RE.sub("", text))


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()

    result: dict[str, str]
    for result in resp.json()["SearchResults"]:
        res.add(
            res.types.MainResult(
                title=_remove_keyword_marker(result["Subject"]),
                content=_remove_keyword_marker(result["Text"]),
                url=result["Url"],
                publishedDate=datetime.strptime(result["Published"], "%Y-%m-%d %H:%M:%S"),
                metadata=gettext.gettext("Posted by {author}").format(author=result["Author"]),
            )
        )

    return res


def fetch_traits(engine_traits: EngineTraits):
    # load main page to be able to find location of JavaScript source code
    resp = get(base_url)
    if resp.status_code != 200:
        raise_for_httperror(resp)

    # load actual JavaScript code
    script_name = "main." + extr(resp.text, "main.", ".js") + ".js"
    script_resp = get(f"{base_url}/{script_name}")
    if script_resp.status_code != 200:
        raise_for_httperror(resp)

    # find list of languages (JavaScript object)
    js_object_string = extr(script_resp.text, "languageValues=", "}],") + "}]"
    languages: list[dict[str, str]] = js_obj_str_to_python(js_object_string)

    # finally, add all parsed languages to the engine traits
    language: dict[str, str]
    for language in languages:
        search_value = language["value"]
        for code in language["codes"]:
            try:
                locale = babel.Locale.parse(code)
            except babel.UnknownLocaleError:
                continue

            sxng_lang = language_tag(locale)
            if sxng_lang not in engine_traits.languages:
                engine_traits.languages[sxng_lang] = search_value

    # "All" is the search value to unset the search language
    engine_traits.all_locale = "All"
