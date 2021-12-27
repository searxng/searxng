# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""CORE (science)

"""

from json import loads
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
    json_data = loads(resp.text)

    for result in json_data['data']:

        source = result['_source']
        time = source['publishedDate'] or source['depositedDate']
        if time:
            date = datetime.fromtimestamp(time / 1000)
        else:
            date = None

        metadata = []
        if source['publisher'] and len(source['publisher']) > 3:
            metadata.append(source['publisher'])
        if source['topics']:
            metadata.append(source['topics'][0])
        if source['doi']:
            metadata.append(source['doi'])
        metadata = ' / '.join(metadata)

        results.append(
            {
                'url': source['urls'][0].replace('http://', 'https://', 1),
                'title': source['title'],
                'content': source['description'],
                'publishedDate': date,
                'metadata': metadata,
            }
        )

    return results
