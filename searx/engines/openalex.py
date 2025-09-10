# SPDX-License-Identifier: AGPL-3.0-or-later
"""The OpenAlex engine integrates the `OpenAlex`_ Works API to return scientific
paper results using the :ref:`result_types.paper` class.  It is an "online" JSON
engine that uses the official public API and does not require an API key.

.. _OpenAlex: https://openalex.org
.. _OpenAlex API overview: https://docs.openalex.org/how-to-use-the-api/api-overview

Key features
------------

- Uses the official Works endpoint (JSON)
- Paging support via ``page`` and ``per-page``
- Relevance sorting (``sort=relevance_score:desc``)
- Language filter support (maps SearXNG language to ``filter=language:<iso2>``)
- Maps fields commonly used in scholarly results: title, authors, abstract
  (reconstructed from inverted index), journal/venue, publisher, DOI, tags
  (concepts), PDF/HTML links, pages, volume, issue, published date, and a short
  citations comment
- Supports OpenAlex "polite pool" by adding a ``mailto`` parameter


Configuration
=============

Minimal example for :origin:`settings.yml <searx/settings.yml>`:

.. code:: yaml

   - name: openalex
     engine: openalex
     shortcut: oa
     categories: science, scientific publications
     timeout: 5.0
     # Recommended by OpenAlex: join the polite pool with an email address
     mailto: "[email protected]"

Notes
-----

- The ``mailto`` key is optional but recommended by OpenAlex for better service.
- Language is inherited from the user's UI language; when it is not ``all``, the
  engine adds ``filter=language:<iso2>`` (e.g. ``language:fr``). If OpenAlex has
  few results for that language, you may see fewer items.
- Results typically include a main link. When the primary landing page from
  OpenAlex is a DOI resolver, the engine will use that stable link. When an open
  access link is available, it is exposed via the ``PDF`` and/or ``HTML`` links
  in the result footer.


What is returned
================

Each result uses the :ref:`result_types.paper` class and may include:

- ``title`` and ``content`` (abstract; reconstructed from the inverted index)
- ``authors`` (display names)
- ``journal`` (host venue display name) and ``publisher``
- ``doi`` (normalized to the plain DOI, without the ``https://doi.org/`` prefix)
- ``tags`` (OpenAlex concepts display names)
- ``pdf_url`` (Open access PDF if available) and ``html_url`` (landing page)
- ``publishedDate`` (parsed from ``publication_date``)
- ``pages``, ``volume``, ``number`` (issue)
- ``type`` and a brief ``comments`` string with citation count


Rate limits & polite pool
=========================

OpenAlex offers a free public API with generous daily limits. For extra courtesy
and improved service quality, include a contact email in each request via
``mailto``. You can set it directly in the engine configuration as shown above.
See: `OpenAlex API overview`_.


Troubleshooting
===============

- Few or no results in a non-English UI language:
  Ensure the selected language has sufficient coverage at OpenAlex, or set the
  UI language to English and retry.
- Preference changes fail while testing locally:
  Make sure your ``server.secret_key`` and ``server.base_url`` are set in your
  instance settings so signed cookies work; see :ref:`settings server`.


Implementation
===============

"""

import typing as t

from datetime import datetime
from urllib.parse import urlencode
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

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


def request(query: str, params: "OnlineParams") -> None:
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


def response(resp: "SXNG_Response") -> EngineResults:
    data = resp.json()
    res = EngineResults()

    for item in data.get("results", []):
        url, html_url, pdf_url = _extract_links(item)
        title: str = item.get("title", "")
        content: str = _reconstruct_abstract(item.get("abstract_inverted_index")) or ""
        authors = _extract_authors(item)
        journal, publisher, pages, volume, number, published_date = _extract_biblio(item)
        doi = _doi_to_plain(item.get("doi"))
        tags = _extract_tags(item)
        comments = _extract_comments(item)

        res.add(
            res.types.Paper(
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


def _stringify_pages(biblio: dict[str, t.Any]) -> str:
    first_page = biblio.get("first_page")
    last_page = biblio.get("last_page")
    if first_page and last_page:
        return f"{first_page}-{last_page}"
    if first_page:
        return str(first_page)
    if last_page:
        return str(last_page)
    return ""


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


def _doi_to_plain(doi_value: str | None) -> str:
    if not doi_value:
        return ""
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


def _extract_links(item: dict[str, t.Any]) -> tuple[str, str, str]:
    primary_location: dict[str, str] = item.get("primary_location", {})
    open_access: dict[str, str] = item.get("open_access", {})

    landing_page_url: str = primary_location.get("landing_page_url") or ""
    work_url: str = item.get("id", "")

    url: str = landing_page_url or work_url
    html_url: str = landing_page_url
    pdf_url: str = primary_location.get("pdf_url") or open_access.get("oa_url") or ""

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
) -> tuple[str, str, str, str, str, datetime | None]:
    host_venue: dict[str, str] = item.get("host_venue", {})
    biblio: dict[str, str] = item.get("biblio", {})

    journal: str = host_venue.get("display_name", "")
    publisher: str = host_venue.get("publisher", "")
    pages: str = _stringify_pages(biblio)
    volume = biblio.get("volume", "")
    number = biblio.get("issue", "")
    published_date = _parse_date(item.get("publication_date"))
    return journal, publisher, pages, volume, number, published_date


def _extract_comments(item: dict[str, t.Any]) -> str:
    cited_by_count = item.get("cited_by_count")
    if isinstance(cited_by_count, int):
        return f"{cited_by_count} citations"
    return ""
