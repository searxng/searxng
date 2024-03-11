# SPDX-License-Identifier: AGPL-3.0-or-later
"""Github (IT)

"""

from urllib.parse import urlencode
from dateutil import parser

# about
about = {
    "website": 'https://github.com/',
    "wikidata_id": 'Q364',
    "official_api_documentation": 'https://developer.github.com/v3/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ['it', 'repos']

# search-url
search_url = 'https://api.github.com/search/repositories?sort=stars&order=desc&{query}'
accept_header = 'application/vnd.github.preview.text-match+json'


def request(query, params):

    params['url'] = search_url.format(query=urlencode({'q': query}))
    params['headers']['Accept'] = accept_header

    return params


def response(resp):
    results = []

    for item in resp.json().get('items', []):
        content = [item.get(i) for i in ['language', 'description'] if item.get(i)]

        # license can be None
        lic = item.get('license') or {}
        lic_url = None
        if lic.get('spdx_id'):
            lic_url = f"https://spdx.org/licenses/{lic.get('spdx_id')}.html"

        results.append(
            {
                'template': 'packages.html',
                'url': item.get('html_url'),
                'title': item.get('full_name'),
                'content': ' / '.join(content),
                'img_src': item.get('owner', {}).get('avatar_url'),
                'package_name': item.get('name'),
                # 'version': item.get('updated_at'),
                'maintainer': item.get('owner', {}).get('login'),
                'publishedDate': parser.parse(item.get("updated_at") or item.get("created_at")),
                'tags': item.get('topics', []),
                'popularity': item.get('stargazers_count'),
                'license_name': lic.get('name'),
                'license_url': lic_url,
                'homepage': item.get('homepage'),
                'source_code_url': item.get('clone_url'),
            }
        )

    return results
