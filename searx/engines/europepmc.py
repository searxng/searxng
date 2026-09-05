# SPDX-License-Identifier: AGPL-3.0-or-later
"""`Europe PMC`_ provides comprehensive access to life sciences literature from
trusted sources.  With Europe PMC you can search and read millions of
publications, preprints and other documents enriched with links to supporting
data, reviews, protocols, and other relevant resources.

.. _Europe PMC: https://europepmc.org/

Configuration
=============

.. code:: yaml

   - name: europepmc
     engine: europepmc
     shortcut: epmc

Implementations
===============

"""

import typing as t

from datetime import datetime
from urllib.parse import urlencode

from dateutil.parser import isoparse

from searx.result_types import EngineResults
from searx.utils import html_to_text

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://europepmc.org/",
    "wikidata_id": "Q5412157",
    "official_api_documentation": "https://europepmc.org/RestfulWebService",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

categories = ["science", "scientific publications"]

# engine dependent config
paging = False
page_size = 900
search_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
article_url = "https://europepmc.org/article/"


def request(query: str, params: "OnlineParams") -> None:
    args = urlencode(
        {
            "query": query,
            "format": "json",
            "resultType": "core",
            "pageSize": page_size,
        }
    )
    params["url"] = f"{search_url}?{args}"


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()

    all_results = resp.json().get("resultList", {}).get("result", [])

    for item in all_results:
        source = item.get("source", "")
        identifier = item.get("id", "")
        url = f"{article_url}{source}/{identifier}" if source and identifier else ""

        journal_info: dict[str, t.Any] = item.get("journalInfo", {})
        journal: dict[str, t.Any] = journal_info.get("journal", {})

        res.add(
            res.types.Paper(
                url=url,
                title=item.get("title", ""),
                content=html_to_text(item.get("abstractText", "")),
                journal=journal.get("title", ""),
                issn=[journal.get("issn", "")],
                authors=_get_authors(item),
                doi=item.get("doi", ""),
                publishedDate=_get_published_date(item),
                type=", ".join((item.get("pubTypeList", {})).get("pubType", [])),
                pdf_url=_get_pdf_url(item),
                html_url=url,
            )
        )

    return res


def _get_authors(item: dict[str, t.Any]) -> list:
    """Extract the list of authors from the item."""
    if authors := item.get("authorString", None):
        authors = [author.strip().rstrip(".") for author in authors.split(",") if author.strip()]
    else:
        authors = []
    return authors


def _get_pdf_url(item: dict[str, t.Any]) -> str:
    """Extract the PDF URL in case it is open access."""
    for url_info in (item.get("fullTextUrlList", {})).get("fullTextUrl", []):
        if url_info.get("documentStyle") == "pdf" and url_info.get("availabilityCode") == "OA":
            return url_info.get("url", "")
    return ""


def _get_published_date(item: dict[str, t.Any]) -> datetime | None:
    """Extract the published date from the item and convert it to a datetime object."""
    if unformatted_date := item.get("firstPublicationDate"):
        return isoparse(unformatted_date)
    return None
