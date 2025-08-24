# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring
#
# Engine is documented in: docs/dev/engines/online/openalex.rst

from __future__ import annotations

import typing as t
from datetime import datetime
from urllib.parse import urlencode
from searx.result_types import EngineResults
from searx.extended_types import SXNG_Response

# about
about = {
    "website": "https://openalex.org/",
    "wikidata_id": "Q110718454",
    "official_api_documentation": "https://docs.openalex.org/how-to-use-the-api/api-overview",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}


# engine dependent config
categories = ["science", "scientific publications"]
paging = True
search_url = "https://api.openalex.org/works"

# Optional: include your email for OpenAlex polite pool. Can be set from settings.yml
# engines: - name: openalex; engine: openalex; mailto: "[email protected]"
mailto = ""


def request(query: str, params: dict[str, t.Any]) -> None:
    # Build OpenAlex query using search parameter and paging
    args = {
        "search": query,
        "page": params["pageno"],
        # keep result size moderate; OpenAlex default is 25
        "per-page": 10,
        # relevance sorting works only with `search`
        "sort": "relevance_score:desc",
    }

    # Language filter (expects ISO639-1 like 'fr', 'en')
    language = params.get("language")
    filters: list[str] = []
    if isinstance(language, str) and language != "all":
        iso2 = language.split("-")[0].split("_")[0]
        if len(iso2) == 2:
            filters.append(f"language:{iso2}")

    if filters:
        args["filter"] = ",".join(filters)

    # include mailto if configured for polite pool (engine module setting)
    if isinstance(mailto, str) and mailto != "":
        args["mailto"] = mailto

    params["url"] = f"{search_url}?{urlencode(args)}"


def response(resp: SXNG_Response) -> EngineResults:
    data = resp.json()
    res = EngineResults()

    for item in data.get("results", []):
        url, html_url, pdf_url = _extract_links(item)
        title: str = item.get("title", "")
        content: str = _reconstruct_abstract(item.get("abstract_inverted_index")) or ""
        authors = _extract_authors(item)
        journal, publisher, pages, volume, number, published_date = _extract_biblio(item)
        doi = _doi_to_plain(item.get("doi"))
        tags = _extract_tags(item) or None
        comments = _extract_comments(item)

        res.add(
            res.types.LegacyResult(
                template="paper.html",
                url=url,
                title=title,
                content=content,
                journal=journal,
                publisher=publisher,
                doi=doi,
                tags=tags,
                authors=authors,
                pdf_url=pdf_url,
                html_url=html_url,
                publishedDate=published_date,
                pages=pages,
                volume=volume,
                number=number,
                type=item.get("type"),
                comments=comments,
            )
        )

    return res


def _stringify_pages(biblio: dict[str, t.Any]) -> str | None:
    first_page = biblio.get("first_page")
    last_page = biblio.get("last_page")
    if first_page and last_page:
        return f"{first_page}-{last_page}"
    if first_page:
        return str(first_page)
    if last_page:
        return str(last_page)
    return None


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    # OpenAlex may return YYYY, YYYY-MM or YYYY-MM-DD
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _doi_to_plain(doi_value: str | None) -> str | None:
    if not doi_value:
        return None
    # OpenAlex `doi` field is commonly a full URL like https://doi.org/10.1234/abcd
    return doi_value.removeprefix("https://doi.org/")


def _reconstruct_abstract(
    abstract_inverted_index: dict[str, list[int]] | None,
) -> str | None:
    # The abstract is returned as an inverted index {token: [positions...]}
    # Reconstruct by placing tokens at their positions and joining with spaces.
    if not abstract_inverted_index:
        return None
    position_to_token: dict[int, str] = {}
    max_index = -1
    for token, positions in abstract_inverted_index.items():
        for pos in positions:
            position_to_token[pos] = token
            max_index = max(max_index, pos)
    if max_index < 0:
        return None
    ordered_tokens = [position_to_token.get(i, "") for i in range(0, max_index + 1)]
    # collapse multiple empty tokens
    text = " ".join(t for t in ordered_tokens if t != "")
    return text if text != "" else None


def _extract_links(item: dict[str, t.Any]) -> tuple[str, str | None, str | None]:
    primary_location = item.get("primary_location", {})
    landing_page_url: str | None = primary_location.get("landing_page_url")
    work_url: str = item.get("id", "")
    url: str = landing_page_url or work_url
    open_access = item.get("open_access", {})
    pdf_url: str | None = primary_location.get("pdf_url") or open_access.get("oa_url")
    html_url: str | None = landing_page_url
    return url, html_url, pdf_url


def _extract_authors(item: dict[str, t.Any]) -> list[str]:
    authors: list[str] = []
    for auth in item.get("authorships", []):
        if not auth:
            continue
        author_obj = auth.get("author", {})
        display_name = author_obj.get("display_name")
        if isinstance(display_name, str) and display_name != "":
            authors.append(display_name)
    return authors


def _extract_tags(item: dict[str, t.Any]) -> list[str]:
    tags: list[str] = []
    for c in item.get("concepts", []):
        name = (c or {}).get("display_name")
        if isinstance(name, str) and name != "":
            tags.append(name)
    return tags


def _extract_biblio(
    item: dict[str, t.Any],
) -> tuple[str | None, str | None, str | None, str | None, str | None, datetime | None]:
    host_venue = item.get("host_venue", {})
    biblio = item.get("biblio", {})
    journal: str | None = host_venue.get("display_name")
    publisher: str | None = host_venue.get("publisher")
    pages = _stringify_pages(biblio)
    volume = biblio.get("volume")
    number = biblio.get("issue")
    published_date = _parse_date(item.get("publication_date"))
    return journal, publisher, pages, volume, number, published_date


def _extract_comments(item: dict[str, t.Any]) -> str | None:
    cited_by_count = item.get("cited_by_count")
    if isinstance(cited_by_count, int):
        return f"{cited_by_count} citations"
    return None
