# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""mwmbl (general)
"""

from urllib.parse import urlencode

about = {
    "website": 'https://github.com/mwmbl/mwmbl',
    "official_api_documentation": None,
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}
paging = False
categories = ['general']

api_url = "https://api.mwmbl.org"


def request(query, params):
    params['url'] = f"{api_url}/search?{urlencode({'s': query})}"
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
