# SPDX-License-Identifier: AGPL-3.0-or-later
"""selfh.st/icons - A collection of logos for self-hosted dashboards and
documentation"""

from dateutil import parser

about = {
    'website': 'https://selfh.st/icons/',
    'official_api_documentation': 'https://selfh.st/icons-about/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}
categories = ['images', 'icons']


icons_list_url = 'https://cdn.selfh.st/directory/icons.json'
icons_cdn_base_url = 'https://cdn.jsdelivr.net'


def request(query, params):
    params['url'] = icons_list_url
    params['query'] = query
    return params


def response(resp):
    results = []

    query_parts = resp.search_params['query'].lower().split(' ')
    for item in resp.json():
        keyword = item['Reference'].lower()
        if not any(query_part in keyword for query_part in query_parts):
            continue

        img_format = None
        for format_name in ('SVG', 'PNG', 'WebP'):
            if item[format_name] == 'Yes':
                img_format = format_name.lower()
                break

        img_src = f'{icons_cdn_base_url}/gh/selfhst/icons/{img_format}/{item["Reference"]}.{img_format}'
        result = {
            'template': 'images.html',
            'url': img_src,
            'title': item['Name'],
            'content': '',
            'img_src': img_src,
            'img_format': img_format,
            'publishedDate': parser.parse(item['CreatedAt']),
        }
        results.append(result)

    return results
