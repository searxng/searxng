# SPDX-License-Identifier: AGPL-3.0-or-later
"""Google Images: see :py:obj:`searx.engines.google`."""

import typing as t
from urllib.parse import parse_qs, unquote, urlparse

from searx.engines.google import fetch_traits  # pylint: disable=unused-import
from searx.engines.google import google_request, wml_dom
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
    )


def response(resp: "SXNG_Response") -> EngineResults:
    results = EngineResults()
    dom = wml_dom(resp)

    for link in eval_xpath_list(dom, '//a[contains(@href, "/imgres?")]'):
        qs = parse_qs(urlparse(link.get("href", "")).query)
        img_src = qs.get("imgurl", [""])[0]
        url = qs.get("imgrefurl", [""])[0]
        if not img_src or not url:
            continue
        width, height = qs.get("w", [""])[0], qs.get("h", [""])[0]
        tbnid = qs.get("tbnid", [""])[0]
        results.add(
            results.types.Image(
                url=url,
                title=unquote(urlparse(img_src).path.rsplit("/", 1)[-1]) or urlparse(url).netloc,
                img_src=img_src,
                thumbnail_src=f"https://encrypted-tbn0.gstatic.com/images?q=tbn:{tbnid}",
                resolution=f"{width} x {height}" if width and height else "",
            )
        )

    return results
