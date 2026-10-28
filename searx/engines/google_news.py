# SPDX-License-Identifier: AGPL-3.0-or-later
"""Google News: see :py:obj:`searx.engines.google`."""

import typing as t

from searx.engines.google import fetch_traits  # pylint: disable=unused-import
from searx.engines.google import google_request, response_dom, unwrap_google_url
from searx.result_types import EngineResults
from searx.utils import eval_xpath_getindex, eval_xpath_list, extract_text

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

# about
about = {
    "website": "https://www.google.com",
    "wikidata_id": "Q12020",
    "official_api_documentation": "https://developers.google.com/custom-search",
    "use_official_api": False,
    "require_api_key": False,
    "results": "XML",
}

# engine dependent config
categories = ["news"]
paging = True
max_page = 50
"""Google supports up to 50 pages of results, see the `Google max_page discussion`_.

.. _Google max_page discussion: https://github.com/searxng/searxng/issues/2982
"""
time_range_support = False
language_support = True
safesearch = False


def request(query: str, params: "OnlineParams") -> None:
    google_request(
        query,
        params,
        {"tbm": "nws"},
        eng_traits=traits,
        use_time_range=False,
        use_safesearch=False,
        use_locales=False,
    )


def response(resp: "SXNG_Response") -> EngineResults:
    results = EngineResults()
    dom = response_dom(resp)
    seen = set()
    for link in eval_xpath_list(dom, '//a[contains(@href, "/url?") and .//span[contains(@class, "CVA68e")]]'):
        url = unwrap_google_url(link.get("href"))
        title = extract_text(eval_xpath_getindex(link, './/span[contains(@class, "CVA68e")]', 0, default=""))
        if not title or url in seen:
            continue
        source = extract_text(eval_xpath_getindex(link, './/span[contains(@class, "dXDvrc")]', 0, default=""))
        when = extract_text(eval_xpath_getindex(link, './/span[contains(@class, "YVIcad")]', 0, default=""))
        snippet = extract_text(
            eval_xpath_getindex(
                link,
                './/span[contains(@class, "FrIlee")]/span[contains(@class, "fYyStc")'
                ' and not(contains(@class, "YVIcad")) and not(contains(@class, "M3vVJe"))'
                ' and not(contains(@class, "dXDvrc"))]',
                0,
                default="",
            )
        )
        seen.add(url)
        results.add(
            results.types.MainResult(
                url=url,
                title=title,
                content=" / ".join(part for part in (source, when, snippet) if part),
            )
        )

    return results
