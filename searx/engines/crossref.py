# SPDX-License-Identifier: AGPL-3.0-or-later
"""Crossref_ is the sustainable source of community-owned scholarly metadata and
is relied upon by thousands of systems across the research ecosystem and the
globe.

.. _Crossref: https://www.crossref.org/documentation/retrieve-metadata/

"""

import typing as t

from urllib.parse import urlencode
from datetime import datetime
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://www.crossref.org/",
    "wikidata_id": "Q5188229",
    "official_api_documentation": "https://api.crossref.org/swagger-ui/",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

categories = ["science", "scientific publications"]
paging = True
search_url = "https://api.crossref.org/works"
"""Returns a list of all works (journal articles, conference proceedings, books,
components, etc), 20 per page (`Works/get_works`_).

.. _Works/get_works: https://api.crossref.org/swagger-ui/index.html#/Works/get_works
"""


def request(query: str, params: "OnlineParams") -> None:
    args = {
        "query": query,
        "offset": 20 * (params["pageno"] - 1),
    }
    params["url"] = f"{search_url}?{urlencode(args)}"


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()
    json_data = resp.json()

    def field(k: str) -> str:
        return str(record.get(k, ""))

    for record in json_data["message"]["items"]:

        if record["type"] == "component":
            # These seem to be files published along with papers. Not something
            # you'd search for.
            continue
        title: str = ""
        journal: str = ""

        if record["type"] == "book-chapter":
            title = record["container-title"][0]
            if record["title"][0].lower().strip() != title.lower().strip():
                title += f" ({record['title'][0]})"
        else:
            title = record["title"][0] if "title" in record else record.get("container-title", [None])[0]
            journal = record.get("container-title", [None])[0] if "title" in record else ""

        item = res.types.Paper(
            title=title,
            journal=journal,
            content=field("abstract"),
            doi=field("DOI"),
            pages=field("page"),
            publisher=field("publisher"),
            tags=record.get("subject"),
            type=field("type"),
            url=field("URL"),
            volume=field("volume"),
        )
        res.add(item)

        if "resource" in record and "primary" in record["resource"] and "URL" in record["resource"]["primary"]:
            item.url = record["resource"]["primary"]["URL"]

        if "published" in record and "date-parts" in record["published"]:
            item.publishedDate = datetime(*(record["published"]["date-parts"][0] + [1, 1][:3]))

        item.authors = [a.get("given", "") + " " + a.get("family", "") for a in record.get("author", [])]
        item.isbn = record.get("isbn") or [i["value"] for i in record.get("isbn-type", [])]

        # All the links are not PDFs, even if the URL ends with ".pdf"
        # item.pdf_url = record.get("link", [{"URL": None}])[0]["URL"]

    return res
