# SPDX-License-Identifier: AGPL-3.0-or-later
"""Picjumbo_ provides free stock photos.

.. _Picjumbo: https://picjumbo.com
"""

from urllib.parse import urlparse, urlunparse
import typing as t

from lxml import html

from searx.result_types import EngineResults
from searx.utils import eval_xpath, eval_xpath_list, extract_text

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://picjumbo.com",
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

base_url = "https://picjumbo.com"

categories = ["images"]
paging = True


def request(query: str, params: "OnlineParams") -> None:
    params["url"] = f"{base_url}/search/{query}/page/{params['pageno']}"


def _get_max_res_url(url: str) -> str:
    """Get the maximum resolution of the image based on the thumbnail URL."""
    parsed_url = urlparse(url)
    max_res_url = parsed_url._replace(query="w=10000&quality=100")
    return urlunparse(max_res_url)


def response(resp: "SXNG_Response"):
    res = EngineResults()

    doc = html.fromstring(resp.text)

    for result in eval_xpath_list(doc, "//div[contains(@class, 'photo_query')]/div[contains(@class, 'photo_item')]"):
        thumbnail = extract_text(eval_xpath(result, ".//img[contains(@class, 'image')]/@src")) or ""
        res.add(
            res.types.Image(
                url=extract_text(eval_xpath(result, ".//a[contains(@class, 'image')]/@href")) or "",
                title=extract_text(eval_xpath(result, ".//h3")) or "",
                content=extract_text(eval_xpath(result, ".//meta[@itemprop='keywords']/@content")) or "",
                thumbnail_src=thumbnail,
                img_src=_get_max_res_url(thumbnail),
            )
        )

    return res
