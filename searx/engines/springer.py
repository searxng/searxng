# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Springer Nature (science)

"""

from datetime import datetime
from json import loads
from urllib.parse import urlencode

from searx.exceptions import SearxEngineAPIException

about = {
    "website": 'https://www.springernature.com/',
    "wikidata_id": 'Q21096327',
    "official_api_documentation": 'https://dev.springernature.com/',
    "use_official_api": True,
    "require_api_key": True,
    "results": 'JSON',
}

categories = ['science', 'scientific publications']
paging = True
nb_per_page = 10
api_key = 'unset'

base_url = 'https://api.springernature.com/metadata/json?'


def request(query, params):
    if api_key == 'unset':
        raise SearxEngineAPIException('missing Springer-Nature API key')
    args = urlencode({'q': query, 's': nb_per_page * (params['pageno'] - 1), 'p': nb_per_page, 'api_key': api_key})
    params['url'] = base_url + args
    logger.debug("query_url --> %s", params['url'])
    return params


def response(resp):
    results = []
    json_data = loads(resp.text)

    for record in json_data['records']:
        published = datetime.strptime(record['publicationDate'], '%Y-%m-%d')
        authors = [" ".join(author['creator'].split(', ')[::-1]) for author in record['creators']]
        tags = record.get('genre')
        if isinstance(tags, str):
            tags = [tags]
        results.append(
            {
                'template': 'paper.html',
                'url': record['url'][0]['value'].replace('http://', 'https://', 1),
                'title': record['title'],
                'content': record['abstract'],
                'comments': record['publicationName'],
                'tags': tags,
                'publishedDate': published,
                'type': record.get('contentType'),
                'authors': authors,
                # 'editor': '',
                'publisher': record.get('publisher'),
                'journal': record.get('publicationName'),
                'volume': record.get('volume') or None,
                'pages': '-'.join([x for x in [record.get('startingPage'), record.get('endingPage')] if x]),
                'number': record.get('number') or None,
                'doi': record.get('doi'),
                'issn': [x for x in [record.get('issn')] if x],
                'isbn': [x for x in [record.get('isbn')] if x],
                # 'pdf_url' : ''
            }
        )
    return results
