# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Semantic Scholar (Science)
"""

from json import dumps, loads
from datetime import datetime

about = {
    "website": 'https://www.semanticscholar.org/',
    "wikidata_id": 'Q22908627',
    "official_api_documentation": 'https://api.semanticscholar.org/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

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
        item = {}
        metadata = []

        url = result.get('primaryPaperLink', {}).get('url')
        if not url and result.get('links'):
            url = result.get('links')[0]
        if not url:
            alternatePaperLinks = result.get('alternatePaperLinks')
            if alternatePaperLinks:
                url = alternatePaperLinks[0].get('url')
        if not url:
            url = paper_url + '/%s' % result['id']

        item['url'] = url

        item['title'] = result['title']['text']
        item['content'] = result['paperAbstract']['text']

        metadata = result.get('fieldsOfStudy') or []
        venue = result.get('venue', {}).get('text')
        if venue:
            metadata.append(venue)
        if metadata:
            item['metadata'] = ', '.join(metadata)

        pubDate = result.get('pubDate')
        if pubDate:
            item['publishedDate'] = datetime.strptime(pubDate, "%Y-%m-%d")

        results.append(item)

    return results
