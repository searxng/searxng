# SPDX-License-Identifier: AGPL-3.0-or-later
"""Google Videos: see :py:obj:`searx.engines.google`."""

import typing as t

from searx.engines.google import fetch_traits  # pylint: disable=unused-import
from searx.engines.google import google_request, response_dom, unwrap_google_url
from searx.result_types import EngineResults
from searx.utils import (
    eval_xpath_getindex,
    eval_xpath_list,
    extract_text,
    parse_duration_string,
)

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

# about
about = {
    "website": "https://www.google.com",
    "wikidata_id": "Q219885",
    "official_api_documentation": "https://developers.google.com/custom-search",
    "use_official_api": False,
    "require_api_key": False,
    "results": "XML",
}

# engine dependent config
categories = ["videos", "web"]
paging = True
max_page = 50
"""Google supports up to 50 pages of results, see the `Google max_page discussion`_.

.. _Google max_page discussion: https://github.com/searxng/searxng/issues/2982
"""
language_support = True
time_range_support = True
safesearch = True


def request(query: str, params: "OnlineParams") -> None:
    google_request(
        query,
        params,
        {"tbm": "vid"},
        eng_traits=traits,
        use_locales=False,
    )


def response(resp: "SXNG_Response") -> EngineResults:
    results = EngineResults()
    dom = response_dom(resp)
    for card in eval_xpath_list(dom, '//div[contains(@class, "zMzFAb") and .//a[contains(@class, "fuLhoc")]]'):
        url = unwrap_google_url(eval_xpath_getindex(card, './/a[contains(@class, "fuLhoc")]/@href', 0))
        title = extract_text(eval_xpath_getindex(card, './/span[contains(@class, "CVA68e")]', 0, default=""))
        if not title:
            continue
        length = None
        for span in eval_xpath_list(card, './/span[contains(@class, "YVIcad")]'):
            length = parse_duration_string(extract_text(span))
            if length:
                break
        results.add(results.types.Video(url=url, title=title, length=length))

    return results
