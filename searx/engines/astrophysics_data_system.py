# SPDX-License-Identifier: AGPL-3.0-or-later
""".. sidebar:: info

The Astrophysics Data System (ADS) is a digital library portal for researchers in astronomy and physics,
operated by the Smithsonian Astrophysical Observatory (SAO) under a NASA grant.
The engine is adapted from the solr engine.

"""

# pylint: disable=global-statement

from datetime import datetime
from json import loads
from urllib.parse import urlencode
from searx.exceptions import SearxEngineAPIException

about = {
    "website": 'https://ui.adsabs.harvard.edu/',
    "wikidata_id": 'Q752099',
    "official_api_documentation": 'https://ui.adsabs.harvard.edu/help/api/api-docs.html',
    "use_official_api": True,
    "require_api_key": True,
    "results": 'JSON',
}

base_url = 'https://api.adsabs.harvard.edu/v1/search'
result_base_url = 'https://ui.adsabs.harvard.edu/abs/'
rows = 10
sort = ''  # sorting: asc or desc
field_list = ['bibcode', 'author', 'title', 'abstract', 'doi', 'date']  # list of field names to display on the UI
default_fields = ''  # default field to query
query_fields = ''  # query fields
paging = True
api_key = 'unset'


def init(_):
    if api_key == 'unset':
        raise SearxEngineAPIException('missing ADS API key')


def request(query, params):
    query_params = {'q': query, 'rows': rows}
    if field_list:
        query_params['fl'] = ','.join(field_list)
    if query_fields:
        query_params['qf'] = ','.join(query_fields)
    if default_fields:
        query_params['df'] = default_fields
    if sort:
        query_params['sort'] = sort

    query_params['start'] = rows * (params['pageno'] - 1)

    params['headers']['Authorization'] = f'Bearer {api_key}'
    params['url'] = f"{base_url}/query?{urlencode(query_params)}"

    return params


def response(resp):
    try:
        resp_json = loads(resp.text)
    except Exception as e:
        raise SearxEngineAPIException("failed to parse response") from e

    if 'error' in resp_json:
        raise SearxEngineAPIException(resp_json['error']['msg'])

    resp_json = resp_json["response"]
    result_len = resp_json["numFound"]
    results = []

    for res in resp_json["docs"]:
        author = res.get("author")

        if author:
            author = author[0] + ' et al.'

        results.append(
            {
                'url': result_base_url + res.get("bibcode") + "/",
                'title': res.get("title")[0],
                'author': author,
                'content': res.get("abstract"),
                'doi': res.get("doi"),
                'publishedDate': datetime.fromisoformat(res.get("date")),
            }
        )

    results.append({'number_of_results': result_len})

    return results
