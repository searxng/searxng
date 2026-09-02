# SPDX-License-Identifier: AGPL-3.0-or-later
"""Europe PMC_ provides comprehensive access to life sciences literature from
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
paging = True
page_size = 20
"""Number of results displayed per SearXNG page."""

api_page_size = 1000
"""Number of results fetched from the Europe PMC API in one request.  The API
does not support offset paging (see module docs), so the engine always
downloads the first ``api_page_size`` results and slices out the requested
page in :py:func:`response`."""

search_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
article_url = "https://europepmc.org/article/"


def request(query: str, params: "OnlineParams") -> None:

    args = urlencode(
        {
            "query": query,
            "format": "json",
            "resultType": "core",
            "pageSize": api_page_size,
        }
    )
    params["url"] = f"{search_url}?{args}"


def response(resp: "SXNG_Response") -> EngineResults:

    res = EngineResults()

    # The API does not support paging (cursorMark only), so every request
    # returns the first api_page_size results; slice out the page SearXNG
    # asked for (same pattern as the ahmia engine).
    pageno: int = resp.search_params.get("pageno", 1) or 1
    start = (pageno - 1) * page_size
    all_results = resp.json().get("resultList", {}).get("result") or []

    for item in all_results[start : start + page_size]:

        source = item.get("source", "")
        identifier = item.get("id", "")
        url = f"{article_url}{source}/{identifier}" if source and identifier else ""

        journal_info: dict[str, t.Any] = item.get("journalInfo", {}) or {}
        journal: dict[str, t.Any] = journal_info.get("journal", {}) or {}

        res.add(
            res.types.Paper(
                url=url,
                title=item.get("title", ""),
                content=_abstract(item.get("abstractText")),
                authors=_authors(item),
                journal=journal.get("title", ""),
                issn=_issn(journal),
                doi=item.get("doi", ""),
                volume=journal_info.get("volume", ""),
                pages=item.get("pageInfo", ""),
                publishedDate=_published_date(item.get("firstPublicationDate")),
                type=_pub_type(item),
                pdf_url=_pdf_url(item),
                html_url=url,
                comments=_citations(item.get("citedByCount")),
            )
        )

    return res


def _abstract(abstract_text: str | None) -> str:
    # Abstracts are returned as HTML (e.g. "<h4>Background</h4>...").
    return html_to_text(abstract_text) if abstract_text else ""


def _authors(item: dict[str, t.Any]) -> list[str]:
    author_list = (item.get("authorList") or {}).get("author") or []
    authors = [a.get("fullName") for a in author_list if isinstance(a.get("fullName"), str)]
    if authors:
        return authors
    # Fall back to the pre-formatted authorString when no structured list.
    author_string = item.get("authorString")
    if isinstance(author_string, str) and author_string:
        return [name.strip() for name in author_string.rstrip(".").split(",")]
    return []


def _issn(journal: dict[str, t.Any]) -> list[str]:
    return [issn for issn in (journal.get("issn"), journal.get("essn")) if isinstance(issn, str) and issn]


def _pub_type(item: dict[str, t.Any]) -> str:
    pub_types = (item.get("pubTypeList") or {}).get("pubType") or []
    return pub_types[0] if pub_types else ""


def _pdf_url(item: dict[str, t.Any]) -> str:
    for url_info in (item.get("fullTextUrlList") or {}).get("fullTextUrl") or []:
        if url_info.get("documentStyle") == "pdf" and url_info.get("availabilityCode") == "OA":
            return url_info.get("url", "")
    return ""


def _citations(cited_by_count: t.Any) -> str:
    if isinstance(cited_by_count, int) and cited_by_count > 0:
        return f"{cited_by_count} citations"
    return ""


def _published_date(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None
