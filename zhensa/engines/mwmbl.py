# SPDX-License-Identifier: AGPL-3.0-or-later
"""Mwmbl_ is a non-profit, ad-free, free-libre and free-lunch search engine with
a focus on useability and speed.

.. hint::

   At the moment it is little more than an idea together with a proof of concept
   implementation of the web front-end and search technology on a small index.
   Mwmbl_ does not support regions, languages, safe-search or time range.
   search.

.. _Mwmbl: https://github.com/mwmbl/mwmbl

"""

from urllib.parse import urlencode

about = {
    "website": 'https://github.com/mwmbl/mwmbl',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}
paging = False
categories = ['general']

api_url = "https://api.mwmbl.org/api/v1"


def request(query, params):
    params['url'] = f"{api_url}/search/?{urlencode({'s': query})}"
    return params


def response(resp):
    results = []

    json_results = resp.json()

    for result in json_results:
        title_parts = [title['value'] for title in result['title']]
        results.append(
            {
                'url': result['url'],
                'title': ''.join(title_parts),
                'content': result['extract'][0]['value'],
            }
        )

    return results
