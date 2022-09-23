# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Semantic Scholar (Science)
"""

from json import dumps, loads
from datetime import datetime

from flask_babel import gettext

about = {
    "website": 'https://www.semanticscholar.org/',
    "wikidata_id": 'Q22908627',
    "official_api_documentation": 'https://api.semanticscholar.org/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ['science', 'scientific publications']
paging = True
search_url = 'https://www.semanticscholar.org/api/1/search'
paper_url = 'https://www.semanticscholar.org/paper'


def request(query, params):
    params['url'] = search_url
    params['method'] = 'POST'
    params['headers']['content-type'] = 'application/json'
    params['data'] = dumps(
        {
            "queryString": query,
            "page": params['pageno'],
            "pageSize": 10,
            "sort": "relevance",
            "useFallbackRankerService": False,
            "useFallbackSearchCluster": False,
            "getQuerySuggestions": False,
            "authors": [],
            "coAuthors": [],
            "venues": [],
            "performTitleMatch": True,
        }
    )
    return params


def response(resp):
    res = loads(resp.text)
    results = []
    for result in res['results']:
        url = result.get('primaryPaperLink', {}).get('url')
        if not url and result.get('links'):
            url = result.get('links')[0]
        if not url:
            alternatePaperLinks = result.get('alternatePaperLinks')
            if alternatePaperLinks:
                url = alternatePaperLinks[0].get('url')
        if not url:
            url = paper_url + '/%s' % result['id']

        # publishedDate
        if 'pubDate' in result:
            publishedDate = datetime.strptime(result['pubDate'], "%Y-%m-%d")
        else:
            publishedDate = None

        # authors
        authors = [author[0]['name'] for author in result.get('authors', [])]

        # pick for the first alternate link, but not from the crawler
        pdf_url = None
        for doc in result.get('alternatePaperLinks', []):
            if doc['linkType'] not in ('crawler', 'doi'):
                pdf_url = doc['url']
                break

        # comments
        comments = None
        if 'citationStats' in result:
            comments = gettext(
                '{numCitations} citations from the year {firstCitationVelocityYear} to {lastCitationVelocityYear}'
            ).format(
                numCitations=result['citationStats']['numCitations'],
                firstCitationVelocityYear=result['citationStats']['firstCitationVelocityYear'],
                lastCitationVelocityYear=result['citationStats']['lastCitationVelocityYear'],
            )

        results.append(
            {
                'template': 'paper.html',
                'url': url,
                'title': result['title']['text'],
                'content': result['paperAbstract']['text'],
                'journal': result.get('venue', {}).get('text') or result.get('journal', {}).get('name'),
                'doi': result.get('doiInfo', {}).get('doi'),
                'tags': result.get('fieldsOfStudy'),
                'authors': authors,
                'pdf_url': pdf_url,
                'publishedDate': publishedDate,
                'comments': comments,
            }
        )

    return results
