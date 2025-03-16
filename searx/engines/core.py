# SPDX-License-Identifier: AGPL-3.0-or-later
"""CORE_ (COnnecting REpositories) provides a comprehensive bibliographic
database of the world’s scholarly literature, collecting and indexing
research from repositories and journals.

.. _CORE: https://core.ac.uk/about

.. _core engine config:

Configuration
=============

The engine has the following additional settings:

- :py:obj:`api_key`

.. code:: yaml

  - name: core.ac.uk
    engine: core
    categories: science
    shortcut: cor
    api_key: "..."
    timeout: 5

Implementations
===============

"""
# pylint: disable=too-many-branches

from datetime import datetime
from urllib.parse import urlencode

from searx.exceptions import SearxEngineAPIException

about = {
    "website": 'https://core.ac.uk',
    "wikidata_id": 'Q22661180',
    "official_api_documentation": 'https://api.core.ac.uk/docs/v3',
    "use_official_api": True,
    "require_api_key": True,
    "results": 'JSON',
}

api_key = 'unset'
"""For an API key register at https://core.ac.uk/services/api and insert
the API key in the engine :ref:`core engine config`."""

categories = ['science', 'scientific publications']
paging = True
nb_per_page = 10
base_url = 'https://api.core.ac.uk/v3/search/works/'


def request(query, params):
    if api_key == 'unset':
        raise SearxEngineAPIException('missing CORE API key')

    # API v3 uses different parameters
    search_params = {
        'q': query,
        'offset': (params['pageno'] - 1) * nb_per_page,
        'limit': nb_per_page,
        'sort': 'relevance',
    }

    params['url'] = base_url + '?' + urlencode(search_params)
    params['headers'] = {'Authorization': f'Bearer {api_key}'}

    return params


def response(resp):
    results = []
    json_data = resp.json()

    for result in json_data.get('results', []):
        # Get title
        if not result.get('title'):
            continue

        # Get URL - try different options
        url = None

        # Try DOI first
        doi = result.get('doi')
        if doi:
            url = f'https://doi.org/{doi}'

        if url is None and result.get('doi'):
            # use the DOI reference
            url = 'https://doi.org/' + str(result['doi'])
        elif result.get('id'):
            url = 'https://core.ac.uk/works/' + str(result['id'])
        elif result.get('downloadUrl'):
            url = result['downloadUrl']
        elif result.get('sourceFulltextUrls'):
            url = result['sourceFulltextUrls']
        else:
            continue

        # Published date
        published_date = None

        raw_date = result.get('publishedDate') or result.get('depositedDate')
        if raw_date:
            try:
                published_date = datetime.fromisoformat(result['publishedDate'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass

        # Handle journals
        journals = []
        if result.get('journals'):
            journals = [j.get('title') for j in result['journals'] if j.get('title')]

        # Handle publisher
        publisher = result.get('publisher', '').strip("'")
        if publisher:
            publisher = publisher.strip("'")

        # Handle authors
        authors = set()
        for i in result.get('authors', []):
            name = i.get("name")
            if name:
                authors.add(name)

        results.append(
            {
                'template': 'paper.html',
                'title': result.get('title'),
                'url': url,
                'content': result.get('fullText', '') or '',
                # 'comments': '',
                'tags': result.get('fieldOfStudy', []),
                'publishedDate': published_date,
                'type': result.get('documentType', '') or '',
                'authors': authors,
                'editor': ', '.join(result.get('contributors', [])),
                'publisher': publisher,
                'journal': ', '.join(journals),
                'doi': result.get('doi'),
                # 'issn' : ''
                # 'isbn' : ''
                'pdf_url': result.get('downloadUrl', {}) or result.get("sourceFulltextUrls", {}),
            }
        )

    return results
