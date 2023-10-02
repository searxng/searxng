# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Pinterest (images)
"""

from json import dumps

about = {
    "website": 'https://www.pinterest.com/',
    "wikidata_id": 'Q255381',
    "official_api_documentation": 'https://developers.pinterest.com/docs/api/v5/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ['images']
paging = True

base_url = 'https://www.pinterest.com'


def request(query, params):
    args = {
        'options': {
            'query': query,
            'bookmarks': [params['engine_data'].get('bookmark', '')],
        },
        'context': {},
    }
    params['url'] = f"{base_url}/resource/BaseSearchResource/get/?data={dumps(args)}"

    return params


def response(resp):
    results = []

    json_resp = resp.json()

    results.append(
        {
            'engine_data': json_resp['resource_response']['bookmark'],
            # it's called bookmark by pinterest, but it's rather a nextpage
            # parameter to get the next results
            'key': 'bookmark',
        }
    )

    for result in json_resp['resource_response']['data']['results']:
        results.append(
            {
                'template': 'images.html',
                'url': result['link'] or f"{base_url}/pin/{result['id']}/",
                'title': result.get('title') or result.get('grid_title'),
                'content': (result.get('rich_summary') or {}).get('display_description') or "",
                'img_src': result['images']['orig']['url'],
                'thumbnail_src': result['images']['236x']['url'],
                'source': (result.get('rich_summary') or {}).get('site_name'),
            }
        )

    return results
