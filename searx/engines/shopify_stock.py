# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shopify stock photos provides royalty-free images, intended for use with
Shopify.
"""

import typing as t
from urllib.parse import urlencode

from lxml import html

from searx.result_types import EngineResults
from searx.utils import eval_xpath, eval_xpath_list, extract_text

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://www.shopify.com/stock-photos",
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

base_url = "https://www.shopify.com"

categories = ["images"]
paging = True


def request(query: str, params: "OnlineParams") -> None:
    args = {"q": query, "page": params["pageno"]}
    params["url"] = f"{base_url}/stock-photos/photos/search?{urlencode(args)}"


def _get_download_url(url: str) -> str:
    """Get the link to the full quality image."""
    query_start = url.find("?")
    return url[:query_start] + "/download?quality=premium"


def response(resp: "SXNG_Response"):
    res = EngineResults()

    doc = html.fromstring(resp.text)

    for result in eval_xpath_list(doc, "//div[contains(@class, 'js-masonry-grid')]/div"):
        url = base_url + (extract_text(eval_xpath(result, ".//a[contains(@class, 'photo-tile')]/@href")) or "")
        res.add(
            res.types.Image(
                url=url,
                title=extract_text(eval_xpath(result, ".//p[contains(@class, 'photo-tile__title')]")) or "",
                thumbnail_src=extract_text(eval_xpath(result, ".//img[contains(@class, 'photo-card__image')]/@src"))
                or "",
                img_src=_get_download_url(url),
            )
        )

    return res
