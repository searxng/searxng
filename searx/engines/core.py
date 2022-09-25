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

categories = ['science', 'scientific publications']
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

    return params


def response(resp):
    results = []
    json_data = resp.json()

    for result in json_data['data']:
        source = result['_source']
        url = None
        if source.get('urls'):
            url = source['urls'][0].replace('http://', 'https://', 1)

        if url is None and source.get('doi'):
            # use the DOI reference
            url = 'https://doi.org/' + source['doi']

        if url is None and source.get('downloadUrl'):
            # use the downloadUrl
            url = source['downloadUrl']

        if url is None and source.get('identifiers'):
            # try to find an ark id, see
            # https://www.wikidata.org/wiki/Property:P8091
            # and https://en.wikipedia.org/wiki/Archival_Resource_Key
            arkids = [
                identifier[5:]  # 5 is the length of "ark:/"
                for identifier in source.get('identifiers')
                if isinstance(identifier, str) and identifier.startswith('ark:/')
            ]
            if len(arkids) > 0:
                url = 'https://n2t.net/' + arkids[0]

        if url is None:
            continue

        publishedDate = None
        time = source['publishedDate'] or source['depositedDate']
        if time:
            publishedDate = datetime.fromtimestamp(time / 1000)

        # sometimes the 'title' is None / filter None values
        journals = [j['title'] for j in (source.get('journals') or []) if j['title']]

        publisher = source['publisher']
        if publisher:
            publisher = source['publisher'].strip("'")

        results.append(
            {
                'template': 'paper.html',
                'title': source['title'],
                'url': url,
                'content': source['description'] or '',
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
                'issn': [x for x in [source.get('issn')] if x],
                'isbn': [x for x in [source.get('isbn')] if x],  # exists in the rawRecordXml
                'pdf_url': source.get('repositoryDocument', {}).get('pdfOrigin'),
            }
        )

    return results
