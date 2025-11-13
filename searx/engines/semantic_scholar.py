# SPDX-License-Identifier: AGPL-3.0-or-later
"""`Semantic Scholar`_ provides free, AI-driven search and discovery tools, and
open resources for the global research community.  `Semantic Scholar`_ index
over 200 million academic papers sourced from publisher partnerships, data
providers, and web crawls.

.. _Semantic Scholar: https://www.semanticscholar.org/about

Configuration
=============

To get in use of this engine add the following entry to your engines list in
``settings.yml``:

.. code:: yaml

   - name: semantic scholar
     engine: semantic_scholar
     shortcut: se

Implementations
===============

"""

import typing as t

from datetime import datetime
from lxml import html
from flask_babel import gettext  # pyright: ignore[reportUnknownVariableType]

from searx.network import get
from searx.utils import eval_xpath_getindex, html_to_text
from searx.enginelib import EngineCache
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://www.semanticscholar.org/",
    "wikidata_id": "Q22908627",
    "official_api_documentation": "https://api.semanticscholar.org/",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

categories = ["science", "scientific publications"]
paging = True
search_url = "https://www.semanticscholar.org/api/1/search"
base_url = "https://www.semanticscholar.org"

CACHE: EngineCache
"""Persistent (SQLite) key/value cache that deletes its values after ``expire``
seconds."""


def setup(engine_settings: dict[str, t.Any]) -> bool:
    global CACHE  # pylint: disable=global-statement
    CACHE = EngineCache(engine_settings["name"])
    return True


def get_ui_version() -> str:
    ret_val: str = CACHE.get("X-S2-UI-Version")
    if not ret_val:
        resp = get(base_url, timeout=3)
        if not resp.ok:
            raise RuntimeError("Can't determine Semantic Scholar UI version")

        doc = html.fromstring(resp.text)
        ret_val = eval_xpath_getindex(doc, "//meta[@name='s2-ui-version']/@content", 0)
        if not ret_val:
            raise RuntimeError("Can't determine Semantic Scholar UI version")
        # hold the cached value for 5min
        CACHE.set("X-S2-UI-Version", value=ret_val, expire=300)
        logger.debug("X-S2-UI-Version: %s", ret_val)
    return ret_val


def request(query: str, params: "OnlineParams") -> None:
    params["url"] = search_url
    params["method"] = "POST"
    params["headers"].update(
        {
            "Content-Type": "application/json",
            "X-S2-UI-Version": get_ui_version(),
            "X-S2-Client": "webapp-browser",
        }
    )
    params["json"] = {
        "queryString": query,
        "page": params["pageno"],
        "pageSize": 10,
        "sort": "relevance",
        "getQuerySuggestions": False,
        "authors": [],
        "coAuthors": [],
        "venues": [],
        "performTitleMatch": True,
    }


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()
    json_data = resp.json()

    for result in json_data["results"]:
        url: str = result.get("primaryPaperLink", {}).get("url")
        if not url and result.get("links"):
            url = result.get("links")[0]
        if not url:
            alternatePaperLinks = result.get("alternatePaperLinks")
            if alternatePaperLinks:
                url = alternatePaperLinks[0].get("url")
        if not url:
            url = base_url + "/paper/%s" % result["id"]

        publishedDate: datetime | None
        if "pubDate" in result:
            publishedDate = datetime.strptime(result["pubDate"], "%Y-%m-%d")
        else:
            publishedDate = None

        # authors
        authors: list[str] = [author[0]["name"] for author in result.get("authors", [])]

        # pick for the first alternate link, but not from the crawler
        pdf_url: str = ""
        for doc in result.get("alternatePaperLinks", []):
            if doc["linkType"] not in ("crawler", "doi"):
                pdf_url = doc["url"]
                break

        # comments
        comments: str = ""
        if "citationStats" in result:
            comments = gettext(
                "{numCitations} citations from the year {firstCitationVelocityYear} to {lastCitationVelocityYear}"
            ).format(
                numCitations=result["citationStats"]["numCitations"],
                firstCitationVelocityYear=result["citationStats"]["firstCitationVelocityYear"],
                lastCitationVelocityYear=result["citationStats"]["lastCitationVelocityYear"],
            )

        res.add(
            res.types.Paper(
                title=result["title"]["text"],
                url=url,
                content=html_to_text(result["paperAbstract"]["text"]),
                journal=result.get("venue", {}).get("text") or result.get("journal", {}).get("name"),
                doi=result.get("doiInfo", {}).get("doi"),
                tags=result.get("fieldsOfStudy"),
                authors=authors,
                pdf_url=pdf_url,
                publishedDate=publishedDate,
                comments=comments,
            )
        )

    return res
