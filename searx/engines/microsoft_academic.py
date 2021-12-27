# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Microsoft Academic (Science)
"""

from json import dumps, loads
from searx.utils import html_to_text

# about
about = {
    "website": 'https://academic.microsoft.com',
    "wikidata_id": 'Q28136779',
    "official_api_documentation": 'http://ma-graph.org/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ['images']
paging = True
search_url = 'https://academic.microsoft.com/api/search'
_paper_url = 'https://academic.microsoft.com/paper/{id}/reference'


def request(query, params):
    params['url'] = search_url
    params['method'] = 'POST'
    params['headers']['content-type'] = 'application/json; charset=utf-8'
    params['data'] = dumps(
        {
            'query': query,
            'queryExpression': '',
            'filters': [],
            'orderBy': 0,
            'skip': (params['pageno'] - 1) * 10,
            'sortAscending': True,
            'take': 10,
            'includeCitationContexts': False,
            'profileId': '',
        }
    )

    return params


def response(resp):
    results = []
    response_data = loads(resp.text)
    if not response_data:
        return results

    for result in response_data.get('pr', {}):
        if 'dn' not in result['paper']:
            continue

        title = result['paper']['dn']
        content = _get_content(result['paper'])
        url = _paper_url.format(id=result['paper']['id'])
        results.append(
            {
                'url': url,
                'title': html_to_text(title),
                'content': html_to_text(content),
            }
        )

    return results


def _get_content(result):
    if 'd' in result:
        content = result['d']
        if len(content) > 300:
            return content[:300] + '...'
        return content

    return ''
