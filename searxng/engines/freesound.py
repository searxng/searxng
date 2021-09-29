# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Freesound (Sound)
"""

from json import loads
from urllib.parse import urlencode
from datetime import datetime

disabled = True
api_key = ""

# about
about = {
    "website": "https://freesound.org",
    "wikidata_id": "Q835703",
    "official_api_documentation": "https://freesound.org/docs/api",
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
}

# engine dependent config
paging = True

# search url
url = "https://freesound.org/apiv2/"
search_url = (
    url
    + "search/text/?query={query}&page={page}&fields=name,url,download,created,description,type&token={api_key}"
)

embedded_url = '<audio controls><source src="{uri}" type="audio/{ftype}"></audio>'


# search request
def request(query, params):
    params["url"] = search_url.format(
        query=urlencode({"q": query}),
        page=params["pageno"],
        api_key=api_key,
    )
    return params


# get response from search request
def response(resp):
    results = []
    search_res = loads(resp.text)
    # parse results
    for result in search_res.get("results", []):
        title = result["name"]
        content = result["description"][:128]
        publishedDate = datetime.fromisoformat(result["created"])
        uri = result["download"]
        embedded = embedded_url.format(uri=uri, ftype=result["type"])

        # append result
        results.append(
            {
                "url": result["url"],
                "title": title,
                "publishedDate": publishedDate,
                "embedded": embedded,
                "content": content,
            }
        )

    return results
