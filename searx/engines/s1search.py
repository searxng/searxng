# SPDX-License-Identifier: AGPL-3.0-or-later
"""Search engines by System1 (general).

System1 is an advertising company, and provides all its search engines as a
subdomain of ``s1search.co``.  As a result, it has more than 1000 subdomains, of
which some work, and some don't.

Some of the engines get their results from Google, others get them from Yahoo.
"""

import typing as t
from urllib.parse import urlencode, urlparse, parse_qs

from lxml import html

from searx.result_types import EngineResults
from searx.enginelib import EngineCache
from searx.utils import eval_xpath_list, eval_xpath, extract_text

if t.TYPE_CHECKING:
    from searx.search.processors import OnlineParams
    from searx.extended_types import SXNG_Response

about = {
    "website": "https://s1search.co",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

base_url = ""  # alternatively: search.gmx.net
categories = ["general"]

paging = True

CACHE: EngineCache
"""Cache to store verification tokens for pagination."""


def init(_):
    if not base_url:
        raise ValueError("base_url must be set")


def setup(engine_settings: dict[str, t.Any]) -> bool:
    global CACHE  # pylint: disable=global-statement
    CACHE = EngineCache(engine_settings["name"])
    return True


def _cache_key(query: str, pageno: int) -> str:
    return f"{query}|{pageno}"


def request(query: str, params: "OnlineParams"):
    args = {"q": query, "page": params["pageno"]}
    if params["pageno"] > 1:
        sc = CACHE.get(_cache_key(query, params["pageno"]))
        # sc is required for pagination to avoid rate-limits
        if not sc:
            params["url"] = None
            return

        args["sc"] = sc

    params["url"] = f"{base_url}/serp?{urlencode(args)}"


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()

    doc = html.fromstring(resp.text)

    for suggestion in eval_xpath_list(doc, "//div[@class='aylf-yahoo-bottom' or @class='aylf-yahoo-sidebar']/div"):
        res.add(res.types.LegacyResult({"suggestion": extract_text(suggestion)}))

    for result in eval_xpath_list(
        doc, "//div[contains(@class, 'web-yahoo') or contains(@class, 'web-google')]/div[contains(@class, '__result')]"
    ):
        res.add(
            res.types.MainResult(
                url=extract_text(eval_xpath(result, ".//a[contains(@class, 'title')]/@href")),
                title=extract_text(eval_xpath(result, ".//a[contains(@class, 'title')]")),
                content=extract_text(eval_xpath(result, ".//span[contains(@class, 'description') or @class='']")),
            )
        )

    # store pagination keys to be able to access next pages
    for page_href in eval_xpath_list(doc, "//a[contains(@class, 'pagination__num')]"):
        # target_url looks like "/serp?q=test&page=2&sc=RVlBPMDPVhWR20"
        target_url = extract_text(eval_xpath(page_href, "./@href"))
        target_url = parse_qs(urlparse(target_url).query)
        pageno = int(target_url["page"][0])
        sc = target_url["sc"][0]
        CACHE.set(_cache_key(resp.search_params["query"], pageno), sc)

    return res
