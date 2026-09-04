# SPDX-License-Identifier: AGPL-3.0-or-later
"""SearchRockit is an American search engine. It allegedly has its own index,
but the results seem to come from Google."""

import typing as t
from urllib.parse import urlencode
from lxml import html
from dateutil import parser

from searx.result_types import EngineResults
from searx.utils import (
    eval_xpath_list,
    extract_text,
    eval_xpath,
)

if t.TYPE_CHECKING:
    from searx.search.processors import OnlineParams
    from searx.extended_types import SXNG_Response

about = {
    "website": "https://searchrockit.com",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

categories = ["general"]
paging = True

SearchrockitCateg = t.Literal["web", "images", "news"]
searchrockit_categ: SearchrockitCateg = "web"

base_url = "https://searchrockit.com"


def setup(_):
    if searchrockit_categ not in t.get_args(SearchrockitCateg):
        raise ValueError("invalid search category: %s" % searchrockit_categ)


def request(query: str, params: "OnlineParams") -> None:
    args = {"q": query, "p": params["pageno"]}
    params["url"] = f"{base_url}/results/{searchrockit_categ}?{urlencode(args)}"


def response(resp: "SXNG_Response") -> EngineResults:
    doc = html.fromstring(resp.text)
    res = EngineResults()

    match searchrockit_categ:
        case "web" | "news":
            for result in eval_xpath_list(
                doc, "//div[contains(@class, 'results-list')]/div[contains(@class, 'result-item')]"
            ):
                publishedDate = None
                try:
                    d = extract_text(eval_xpath(result, ".//span[contains(@class, 'result-item--publishedAt')]")) or ""
                    publishedDate = parser.parse(d)
                except parser.ParserError:
                    pass
                res.add(
                    res.types.MainResult(
                        url=extract_text(eval_xpath(result, ".//a[contains(@class, 'result-item--title')]/@href")),
                        title=extract_text(eval_xpath(result, ".//a[contains(@class, 'result-item--title')]")) or "",
                        content=extract_text(eval_xpath(result, ".//a[contains(@class, 'result-item--desc')]")) or "",
                        thumbnail=extract_text(
                            eval_xpath(result, ".//a[contains(@class, 'result-item--thumb')]/img/@src")
                        )
                        or "",
                        publishedDate=publishedDate,
                    )
                )
        case "images":
            for result in eval_xpath_list(
                doc, "//div[contains(@class, 'image-grid')]/a[contains(@class, 'image-card')]"
            ):
                res.add(
                    res.types.Image(
                        url=extract_text(eval_xpath(result, "./@href")),
                        title=extract_text(eval_xpath(result, "./div[contains(@class, 'image-title')]")) or "",
                        thumbnail_src=extract_text(eval_xpath(result, "./img/@src")) or "",
                        img_src=extract_text(eval_xpath(result, "./@data-full-url")) or "",
                    )
                )

    return res
