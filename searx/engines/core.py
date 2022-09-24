# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""CORE (science)

"""

from datetime import datetime
from urllib.parse import urlencode

from searx.exceptions import SearxEngineAPIException

about = {
    "website": 'https://core.ac.uk',
    "wikidata_id": 'Q22661180',
    "official_api_documentation": 'https://core.ac.uk/documentation/api/',
    "use_official_api": True,
    "require_api_key": True,
    "results": 'JSON',
}

categories = ['science']
paging = True
nb_per_page = 10

api_key = 'unset'

base_url = 'https://core.ac.uk:443/api-v2/search/'
search_string = '{query}?page={page}&pageSize={nb_per_page}&apiKey={apikey}'


def request(query, params):

    if api_key == 'unset':
        raise SearxEngineAPIException('missing CORE API key')

    search_path = search_string.format(
        query=urlencode({'q': query}),
        nb_per_page=nb_per_page,
        page=params['pageno'],
        apikey=api_key,
    )
    params['url'] = base_url + search_path

    logger.debug("query_url --> %s", params['url'])
    return params


def response(resp):
    results = []
    json_data = resp.json()

    for result in json_data['data']:
        source = result['_source']
        if not source['urls']:
            continue

        time = source['publishedDate'] or source['depositedDate']
        if time:
            publishedDate = datetime.fromtimestamp(time / 1000)

        journals = []
        if source['journals']:
            for j in source['journals']:
                journals.append(j['title'])

        publisher = source['publisher']
        if publisher:
            publisher = source['publisher'].strip("'")

        results.append(
            {
                'template': 'paper.html',
                'title': source['title'],
                'url': source['urls'][0].replace('http://', 'https://', 1),
                'content': source['description'],
                # 'comments': '',
                'tags': source['topics'],
                'publishedDate': publishedDate,
                'type': (source['types'] or [None])[0],
                'authors': source['authors'],
                'editor': ', '.join(source['contributors'] or []),
                'publisher': publisher,
                'journal': ', '.join(journals),
                # 'volume': '',
                # 'pages' : '',
                # 'number': '',
                'doi': source['doi'],
                'issn': source['issn'],
                'isbn': source.get('isbn'),  # exists in the rawRecordXml
                'pdf_url': source.get('repositoryDocument', {}).get('pdfOrigin'),
            }
        )

    return results
