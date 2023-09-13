# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""CrossRef"""

from urllib.parse import urlencode
from datetime import datetime

about = {
    "website": "https://www.crossref.org/",
    "wikidata_id": "Q5188229",
    "official_api_documentation": "https://api.crossref.org",
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

categories = ["science", "scientific publications"]
paging = True
search_url = "https://api.crossref.org/works"


def request(query, params):
    params["url"] = search_url + "?" + urlencode({"query": query, "offset": 20 * (params["pageno"] - 1)})
    return params


def response(resp):
    results = []
    for record in resp.json()["message"]["items"]:

        if record["type"] == "component":
            # These seem to be files published along with papers. Not something you'd search for
            continue
        result = {
            "template": "paper.html",
            "content": record.get("abstract", ""),
            "doi": record.get("DOI"),
            "pages": record.get("page"),
            "publisher": record.get("publisher"),
            "tags": record.get("subject"),
            "type": record.get("type"),
            "url": record.get("URL"),
            "volume": record.get("volume"),
        }
        if record["type"] == "book-chapter":
            result["title"] = record["container-title"][0]
            if record["title"][0].lower().strip() != result["title"].lower().strip():
                result["title"] += f" ({record['title'][0]})"
        else:
            result["title"] = record["title"][0] if "title" in record else record.get("container-title", [None])[0]
            result["journal"] = record.get("container-title", [None])[0] if "title" in record else None

        if "resource" in record and "primary" in record["resource"] and "URL" in record["resource"]["primary"]:
            result["url"] = record["resource"]["primary"]["URL"]
        if "published" in record and "date-parts" in record["published"]:
            result["publishedDate"] = datetime(*(record["published"]["date-parts"][0] + [1, 1][:3]))
        result["authors"] = [a.get("given", "") + " " + a.get("family", "") for a in record.get("author", [])]
        result["isbn"] = record.get("isbn") or [i["value"] for i in record.get("isbn-type", [])]
        # All the links are not PDFs, even if the URL ends with ".pdf"
        # result["pdf_url"] = record.get("link", [{"URL": None}])[0]["URL"]

        results.append(result)

    return results
