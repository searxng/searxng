# SPDX-License-Identifier: AGPL-3.0-or-later
"""Matrix Rooms Search - a fully-featured, standalone, matrix rooms search service.

Configuration
=============

The engine has the following mandatory settings:

- :py:obj:`base_url`

.. code:: yaml

  - name: MRS
    engine: mrs
    base_url: https://mrs-host
    ...

Implementation
==============
"""

from urllib.parse import quote_plus

about = {
    "website": 'https://matrixrooms.info',
    "wikidata_id": None,
    "official_api_documentation": 'https://gitlab.com/etke.cc/mrs/api/-/blob/main/openapi.yml?ref_type=heads',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}
paging = True
categories = ['social media']

base_url = ""
matrix_url = "https://matrix.to"
page_size = 20


def init(engine_settings):  # pylint: disable=unused-argument
    """The ``base_url`` must be set in the configuration, if ``base_url`` is not
    set, a :py:obj:`ValueError` is raised during initialization.

    """
    if not base_url:
        raise ValueError('engine MRS, base_url is unset')


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
