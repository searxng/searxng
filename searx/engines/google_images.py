# SPDX-License-Identifier: AGPL-3.0-or-later
"""Google Images: see :py:obj:`searx.engines.google`."""

import typing as t
from urllib.parse import parse_qs, urlparse

from searx.engines.google import fetch_traits  # pylint: disable=unused-import
from searx.engines.google import google_request, response_dom
from searx.result_types import EngineResults
from searx.utils import eval_xpath_list

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

# about
about = {
    "website": "https://images.google.com",
    "wikidata_id": "Q521550",
    "official_api_documentation": "https://developers.google.com/custom-search",
    "use_official_api": False,
    "require_api_key": False,
    "results": "XML",
}

# engine dependent config
categories = ["images", "web"]
paging = True
enable_http3 = True
max_page = 50
"""Google supports up to 50 pages of results, see the `Google max_page discussion`_.

.. _Google max_page discussion: https://github.com/searxng/searxng/issues/2982
"""

time_range_support = True
language_support = True
safesearch = True

filter_mapping = {0: "images", 1: "active", 2: "active"}


def request(query: str, params: "OnlineParams") -> None:
    google_request(
        query,
        params,
        {"tbm": "isch"},
        eng_traits=traits,
        safesearch_map=filter_mapping,
        use_locales=False,
        images=True,
    )


def response(resp: "SXNG_Response") -> EngineResults:
    results = EngineResults()
    dom = response_dom(resp)

    for link in eval_xpath_list(dom, '//a[contains(@href, "/imgres?")]'):
        query = parse_qs(urlparse(link.get("href")).query)
        page_url = query["imgrefurl"][0]
        image = link.xpath(".//img")[0]
        host = urlparse(page_url).netloc.removeprefix("www.")
        results.add(
            results.types.Image(
                url=page_url,
                title=(image.get("alt") or "").strip() or host,
                img_src=query["imgurl"][0],
                thumbnail_src=image.get("src"),
                resolution=f"{query['w'][0]} x {query['h'][0]}",
            )
        )

    return results
