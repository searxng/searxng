# SPDX-License-Identifier: AGPL-3.0-or-later
"""OpenAlex (Scientific works)

References:
- API overview: https://docs.openalex.org/how-to-use-the-api/api-overview

The engine queries the OpenAlex Works endpoint and maps fields to the
`paper.html` result template.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

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


def _stringify_pages(biblio: Dict[str, Any]) -> Optional[str]:
    first_page = biblio.get("first_page")
    last_page = biblio.get("last_page")
    if first_page and last_page:
        return f"{first_page}-{last_page}"
    if first_page:
        return str(first_page)
    if last_page:
        return str(last_page)
    return None


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    # OpenAlex may return YYYY, YYYY-MM or YYYY-MM-DD
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _doi_to_plain(doi_value: Optional[str]) -> Optional[str]:
    if not doi_value:
        return None
    # OpenAlex `doi` field is commonly a full URL like https://doi.org/10.1234/abcd
    return doi_value.removeprefix("https://doi.org/")


def _reconstruct_abstract(
    abstract_inverted_index: Optional[Dict[str, List[int]]],
) -> Optional[str]:
    # The abstract is returned as an inverted index {token: [positions...]}
    # Reconstruct by placing tokens at their positions and joining with spaces.
    if not abstract_inverted_index:
        return None
    position_to_token: Dict[int, str] = {}
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


def request(query, params):
    # Build OpenAlex query using search parameter and paging
    args: Dict[str, Any] = {
        "search": query,
        "page": params["pageno"],
        # keep result size moderate; OpenAlex default is 25
        "per-page": 10,
        # relevance sorting works only with `search`
        "sort": "relevance_score:desc",
    }

    # Language filter (expects ISO639-1 like 'fr', 'en')
    language = params.get("language")
    filters: List[str] = []
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
    return params


def _extract_links(item: Dict[str, Any]) -> tuple[str, Optional[str], Optional[str]]:
    primary_location = item.get("primary_location", {})
    landing_page_url: Optional[str] = primary_location.get("landing_page_url")
    work_url: str = item.get("id", "")
    url: str = landing_page_url or work_url
    open_access = item.get("open_access", {})
    pdf_url: Optional[str] = primary_location.get("pdf_url") or open_access.get("oa_url")
    html_url: Optional[str] = landing_page_url
    return url, html_url, pdf_url


def _extract_authors(item: Dict[str, Any]) -> List[str]:
    authors: List[str] = []
    for auth in item.get("authorships", []):
        if not auth:
            continue
        author_obj = auth.get("author", {})
        display_name = author_obj.get("display_name")
        if isinstance(display_name, str) and display_name != "":
            authors.append(display_name)
    return authors


def _extract_tags(item: Dict[str, Any]) -> List[str]:
    tags: List[str] = []
    for c in item.get("concepts", []):
        name = (c or {}).get("display_name")
        if isinstance(name, str) and name != "":
            tags.append(name)
    return tags


def _extract_biblio(
    item: Dict[str, Any],
) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[datetime]]:
    host_venue = item.get("host_venue", {})
    biblio = item.get("biblio", {})
    journal: Optional[str] = host_venue.get("display_name")
    publisher: Optional[str] = host_venue.get("publisher")
    pages = _stringify_pages(biblio)
    volume = biblio.get("volume")
    number = biblio.get("issue")
    published_date = _parse_date(item.get("publication_date"))
    return journal, publisher, pages, volume, number, published_date


def _extract_comments(item: Dict[str, Any]) -> Optional[str]:
    cited_by_count = item.get("cited_by_count")
    if isinstance(cited_by_count, int):
        return f"{cited_by_count} citations"
    return None


def response(resp):
    res = resp.json()
    results: List[Dict[str, Any]] = []

    for item in res.get("results", []):
        url, html_url, pdf_url = _extract_links(item)
        title: str = item.get("title", "")
        content: str = _reconstruct_abstract(item.get("abstract_inverted_index")) or ""
        authors = _extract_authors(item)
        journal, publisher, pages, volume, number, published_date = _extract_biblio(item)
        doi = _doi_to_plain(item.get("doi"))
        tags = _extract_tags(item) or None
        comments = _extract_comments(item)

        results.append(
            {
                "template": "paper.html",
                "url": url,
                "title": title,
                "content": content,
                "journal": journal,
                "publisher": publisher,
                "doi": doi,
                "tags": tags,
                "authors": authors,
                "pdf_url": pdf_url,
                "html_url": html_url,
                "publishedDate": published_date,
                "pages": pages,
                "volume": volume,
                "number": number,
                "type": item.get("type"),
                "comments": comments,
            }
        )

    return results
