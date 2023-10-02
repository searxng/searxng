# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Matrixrooms.info (social media)
"""

from urllib.parse import quote_plus

about = {
    "website": 'https://matrixrooms.info',
    "wikidata_id": 'Q107565255',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}
paging = True
categories = ['social media']

base_url = "https://apicdn.matrixrooms.info"
matrix_url = "https://matrix.to"
page_size = 20


def request(query, params):
    params['url'] = f"{base_url}/search/{quote_plus(query)}/{page_size}/{(params['pageno']-1)*page_size}"
    return params


def response(resp):
    results = []

    for result in resp.json():
        results.append(
            {
                'url': matrix_url + '/#/' + result['alias'],
                'title': result['name'],
                'content': result['topic']
                + f" // {result['members']} members"
                + f" // {result['alias']}"
                + f" // {result['server']}",
                'thumbnail': result['avatar_url'],
            }
        )

    return results
