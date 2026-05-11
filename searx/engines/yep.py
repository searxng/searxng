# SPDX-License-Identifier: AGPL-3.0-or-later
"""Yep (general, images, news)"""

import re

import typing as t

from urllib.parse import urlencode

from searx.result_types import EngineResults
from searx.utils import html_to_text, eval_xpath_getindex, extract_text

if t.TYPE_CHECKING:
    from searx.enginelib.traits import EngineTraits
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    'website': 'https://yep.com/',
    'official_api_documentation': 'https://docs.developer.yelp.com',
    'use_official_api': False,
    'require_api_key': False,
    'results': 'JSON',
}

base_url = "https://api.yep.com"

safesearch = True
safesearch_map = {0: 'off', 1: 'moderate', 2: 'strict'}

enable_http2 = False

results_per_page = 20

_IMPORT_RE = re.compile(r"import\"(.*?)\";")
_LANGUAGE_RE = re.compile(r"\{english:\".*?\",code_string:\"(.*?)\",code:\".*?\"\}")


def request(query: str, params: 'OnlineParams') -> None:
    args = {'query': query, 'safeSearch': safesearch_map[params['safesearch']], 'limit': results_per_page}

    engine_language: str = traits.get_language(params["searxng_locale"])
    if engine_language:
        args["hl"] = engine_language

    params['url'] = f"{base_url}/fs/2/search?{urlencode(args)}"
    params['headers']['Referer'] = 'https://yep.com/'
    params['headers']['Origin'] = 'https://yep.com'


def response(resp: 'SXNG_Response') -> EngineResults:
    res = EngineResults()

    for result in resp.json()[1]['results']:
        res.add(
            res.types.MainResult(
                url=result['url'],
                title=result['title'],
                content=html_to_text(result['snippet']),
            )
        )

    return res


def fetch_traits(engine_traits: 'EngineTraits'):
    """Fetch :ref:`languages <yep languages>` and :ref:`regions <yep
    regions>` from Yep.

    The language options are very well hidden on Yep. To get it, we have to do the following:
    - Load the yep.com mainpage and extract the URL of the JavaScript app
    - Load the JavaScript source code and extract the URL of all imported modules from it
    - Load the imported modules to search for the right one that contains the languages
    """

    # pylint: disable=import-outside-toplevel, too-many-branches

    from lxml import html
    import babel

    from searx.locales import language_tag
    from searx.network import get  # see https://github.com/searxng/searxng/issues/762

    from searx.utils import gen_useragent

    web_base_url = "https://yep.com"

    headers = {
        "User-Agent": gen_useragent(),
        "Referer": f"{web_base_url}/",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
    }

    resp = get(web_base_url, headers=headers, timeout=5)
    if not resp.ok:
        raise RuntimeError("Response from Yep languages is not OK.")

    doc = html.fromstring(resp.text)
    url = eval_xpath_getindex(doc, "//script[contains(@src, 'PageApp')]/@src", index=0)

    resp = get("https:" + extract_text(url), headers=headers, timeout=5)
    if not resp.ok:
        raise RuntimeError("Response from Yep languages is not OK.")

    language_codes = []
    for script_path in _IMPORT_RE.findall(resp.text):
        resp = get(f"{web_base_url}{script_path}", headers=headers, timeout=5)
        if not resp.ok:
            raise RuntimeError("Response from Yep languages is not OK.")

        for match in _LANGUAGE_RE.findall(resp.text):
            language_codes.append(match)

        if language_codes:
            break

    for language_code in language_codes:
        try:
            sxng_tag = language_tag(babel.Locale.parse(language_code, sep="-"))
        except babel.UnknownLocaleError:
            # silently ignore unknown languages
            continue
        # print("%-20s: %s <-- %s" % (extract_text(option), country_tag, sxng_tag))

        conflict = engine_traits.languages.get(sxng_tag)
        if conflict:
            if conflict != sxng_tag:
                print("CONFLICT: babel %s --> %s, %s" % (sxng_tag, conflict, language_code))
            continue
        engine_traits.languages[sxng_tag] = language_code
