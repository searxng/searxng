# SPDX-License-Identifier: AGPL-3.0-or-later
"""Google Images: see :py:obj:`searx.engines.google`."""

import typing as t

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

    for tile in eval_xpath_list(
        dom,
        '//div[contains(@class, "islrtb") and @data-ou and @data-ru and @data-pt'
        ' and @data-tbnid and @data-ow and @data-oh]',
    ):
        results.add(
            results.types.Image(
                url=tile.get("data-ru"),
                title=tile.get("data-pt"),
                img_src=tile.get("data-ou"),
                thumbnail_src=f"https://encrypted-tbn0.gstatic.com/images?q=tbn:{tile.get('data-tbnid')}",
                resolution=f"{tile.get('data-ow')} x {tile.get('data-oh')}",
            )
        )

    return results
