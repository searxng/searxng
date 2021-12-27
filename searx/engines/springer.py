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

categories = ['science']
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
        content = record['abstract'][0:500]
        if len(record['abstract']) > len(content):
            content += "..."
        published = datetime.strptime(record['publicationDate'], '%Y-%m-%d')

        metadata = [
            record[x]
            for x in [
                'publicationName',
                'identifier',
                'contentType',
            ]
            if record.get(x) is not None
        ]

        metadata = ' / '.join(metadata)
        if record.get('startingPage') and record.get('endingPage') is not None:
            metadata += " (%(startingPage)s-%(endingPage)s)" % record

        results.append(
            {
                'title': record['title'],
                'url': record['url'][0]['value'].replace('http://', 'https://', 1),
                'content': content,
                'publishedDate': published,
                'metadata': metadata,
            }
        )
    return results
