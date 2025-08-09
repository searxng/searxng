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
    if value is None or value == "":
        return None
    # OpenAlex may return YYYY, YYYY-MM or YYYY-MM-DD
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _doi_to_plain(doi_value: Optional[str]) -> Optional[str]:
    if doi_value is None or doi_value == "":
        return None
    # OpenAlex `doi` field is commonly a full URL like https://doi.org/10.1234/abcd
    prefix = "https://doi.org/"
    if doi_value.startswith(prefix):
        return doi_value[len(prefix) :]
    return doi_value


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
            if pos > max_index:
                max_index = pos
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

    # include mailto if configured for polite pool; else use a sane default if provided in params
    mailto_setting = params.get("mailto") or globals().get("mailto")
    if isinstance(mailto_setting, str) and mailto_setting != "":
        args["mailto"] = mailto_setting

    params["url"] = f"{search_url}?{urlencode(args)}"
    return params


def response(resp):
    res = resp.json()
    results: List[Dict[str, Any]] = []

    for item in res.get("results", []):
        # Prefer the landing page URL; fallback to OpenAlex work URL (id)
        primary_location = item.get("primary_location") or {}
        host_venue = item.get("host_venue") or {}
        biblio = item.get("biblio") or {}
        concepts = item.get("concepts") or []
        open_access = item.get("open_access") or {}

        landing_page_url: Optional[str] = primary_location.get("landing_page_url")
        work_url: str = item.get("id", "")
        url: str = landing_page_url or work_url

        # Title and abstract
        title: str = item.get("title") or ""
        content: Optional[str] = _reconstruct_abstract(
            item.get("abstract_inverted_index")
        )

        # Authors
        authorships = item.get("authorships") or []
        authors: List[str] = []
        for auth in authorships:
            author_obj = (auth or {}).get("author") or {}
            display_name = author_obj.get("display_name")
            if isinstance(display_name, str) and display_name != "":
                authors.append(display_name)

        # Journal and publisher
        journal: Optional[str] = host_venue.get("display_name")
        publisher: Optional[str] = host_venue.get("publisher")

        # DOI
        doi: Optional[str] = _doi_to_plain(item.get("doi"))

        # Links
        pdf_url: Optional[str] = primary_location.get("pdf_url") or open_access.get(
            "oa_url"
        )
        html_url: Optional[str] = landing_page_url

        # Tags from concepts
        tags: List[str] = []
        for c in concepts:
            name = (c or {}).get("display_name")
            if isinstance(name, str) and name != "":
                tags.append(name)

        # Dates and biblio
        published_date = _parse_date(item.get("publication_date"))
        pages = _stringify_pages(biblio)
        volume = biblio.get("volume")
        number = biblio.get("issue")

        # Type and comments
        work_type: Optional[str] = item.get("type")
        cited_by_count = item.get("cited_by_count")
        comments: Optional[str] = None
        if isinstance(cited_by_count, int):
            comments = f"{cited_by_count} citations"

        results.append(
            {
                "template": "paper.html",
                "url": url,
                "title": title,
                "content": content or "",
                "journal": journal,
                "publisher": publisher,
                "doi": doi,
                "tags": tags or None,
                "authors": authors,
                "pdf_url": pdf_url,
                "html_url": html_url,
                "publishedDate": published_date,
                "pages": pages,
                "volume": volume,
                "number": number,
                "type": work_type,
                "comments": comments,
            }
        )

    return results
