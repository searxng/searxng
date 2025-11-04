# SPDX-License-Identifier: AGPL-3.0-or-later
"""Engine to search in the collaborative software platform SourceHut_.

.. _SourceHut: https://sourcehut.org/

Configuration
=============

You can configure the following setting:

- :py:obj:`sourcehut_sort_order`

.. code:: yaml

  - name: sourcehut
    shortcut: srht
    engine: sourcehut
    # sourcehut_sort_order: longest-active

Implementations
===============

"""

import typing as t

from urllib.parse import urlencode
from lxml import html

from searx.utils import eval_xpath, eval_xpath_list, extract_text, searxng_useragent
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://sourcehut.org",
    "wikidata_id": "Q78514485",
    "official_api_documentation": "https://man.sr.ht/",
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

categories = ["it", "repos"]
paging = True

base_url: str = "https://sr.ht/projects"
"""Browse public projects."""


sourcehut_sort_order: str = "recently-updated"
"""The sort order of the results.  Possible values:

- ``recently-updated``
- ``longest-active``
"""


def request(query: str, params: "OnlineParams") -> None:

    args = {"search": query, "page": params["pageno"], "sort": sourcehut_sort_order}
    params["url"] = f"{base_url}?{urlencode(args)}"

    # standard user agents are blocked by 'go-away', a foss bot detection tool
    params["headers"]["User-Agent"] = searxng_useragent()


def response(resp: "SXNG_Response") -> EngineResults:

    res = EngineResults()
    doc = html.fromstring(resp.text)

    for item in eval_xpath_list(doc, "(//div[@class='event-list'])[1]/div[contains(@class, 'event')]"):
        res.add(
            res.types.LegacyResult(
                template="packages.html",
                url=base_url + (extract_text(eval_xpath(item, "./h4/a[2]/@href")) or ""),
                title=extract_text(eval_xpath(item, "./h4")),
                package_name=extract_text(eval_xpath(item, "./h4/a[2]")),
                content=extract_text(eval_xpath(item, "./p")),
                maintainer=(extract_text(eval_xpath(item, "./h4/a[1]")) or "").removeprefix("~"),
                tags=[
                    tag.removeprefix("#") for tag in eval_xpath_list(item, "./div[contains(@class, 'tags')]/a/text()")
                ],
            )
        )
    return res
