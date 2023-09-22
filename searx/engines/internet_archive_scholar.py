# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Internet Archive scholar(science)
"""

from datetime import datetime
from urllib.parse import urlencode
from searx.utils import html_to_text

about = {
    "website": "https://scholar.archive.org/",
    "wikidata_id": "Q115667709",
    "official_api_documentation": "https://scholar.archive.org/api/redoc",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}
categories = ['science', 'scientific publications']
paging = True

base_url = "https://scholar.archive.org"
results_per_page = 15


def request(query, params):
    args = {
        "q": query,
        "limit": results_per_page,
        "offset": (params["pageno"] - 1) * results_per_page,
    }
    params["url"] = f"{base_url}/search?{urlencode(args)}"
    params["headers"]["Accept"] = "application/json"
    return params


def response(resp):
    results = []

    json = resp.json()

    for result in json["results"]:
        publishedDate, content, doi = None, '', None

        if result['biblio'].get('release_date'):
            publishedDate = datetime.strptime(result['biblio']['release_date'], "%Y-%m-%d")

        if len(result['abstracts']) > 0:
            content = result['abstracts'][0].get('body')
        elif len(result['_highlights']) > 0:
            content = result['_highlights'][0]

        if len(result['releases']) > 0:
            doi = result['releases'][0].get('doi')

        results.append(
            {
                'template': 'paper.html',
                'url': result['fulltext']['access_url'],
                'title': result['biblio'].get('title') or result['biblio'].get('container_name'),
                'content': html_to_text(content),
                'publisher': result['biblio'].get('publisher'),
                'doi': doi,
                'journal': result['biblio'].get('container_name'),
                'authors': result['biblio'].get('contrib_names'),
                'tags': result['tags'],
                'publishedDate': publishedDate,
                'issns': result['biblio'].get('issns'),
                'pdf_url': result['fulltext'].get('access_url'),
            }
        )

    return results
