# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Semantic Scholar (Science)
"""
# pylint: disable=use-dict-literal

from urllib.parse import urlencode
from searx.utils import html_to_text

about = {
    "website": 'https://www.crossref.org/',
    "wikidata_id": 'Q5188229',
    "official_api_documentation": 'https://github.com/CrossRef/rest-api-doc',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ['science', 'scientific publications']
paging = True
search_url = 'https://api.crossref.org/works'


def request(query, params):
    params['url'] = search_url + '?' + urlencode(dict(query=query, offset=20 * (params['pageno'] - 1)))
    return params


def response(resp):
    res = resp.json()
    results = []
    for record in res['message']['items']:
        record_type = record['type']
        if record_type == 'book-chapter':
            title = record['container-title'][0]
            if record['title'][0].lower().strip() != title.lower().strip():
                title = html_to_text(title) + ' (' + html_to_text(record['title'][0]) + ')'
            journal = None
        else:
            title = html_to_text(record['title'][0])
            journal = record.get('container-title', [None])[0]
        url = record.get('resource', {}).get('primary', {}).get('URL') or record['URL']
        authors = [author.get('given', '') + ' ' + author.get('family', '') for author in record.get('author', [])]
        isbn = record.get('isbn') or [i['value'] for i in record.get('isbn-type', [])]
        results.append(
            {
                'template': 'paper.html',
                'url': url,
                'title': title,
                'journal': journal,
                'volume': record.get('volume'),
                'type': record['type'],
                'content': html_to_text(record.get('abstract', '')),
                'publisher': record.get('publisher'),
                'authors': authors,
                'doi': record['DOI'],
                'isbn': isbn,
            }
        )
    return results
