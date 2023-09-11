# SPDX-License-Identifier: AGPL-3.0-or-later
"""Library of Congress: query Photo, Print and Drawing from API endpoint_
``photos``.

.. _endpoint: https://www.loc.gov/apis/json-and-yaml/requests/endpoints/

.. note::

   Beside the ``photos`` endpoint_ there are more endpoints available / we are
   looking forward for contributions implementing more endpoints.

"""

from urllib.parse import urlencode
from searx.network import raise_for_httperror

about = {
    "website": 'https://www.loc.gov/pictures/',
    "wikidata_id": 'Q131454',
    "official_api_documentation": 'https://www.loc.gov/api',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ['images']
paging = True

endpoint = 'photos'
base_url = 'https://loc.gov'
search_string = "/{endpoint}/?sp={page}&{query}&fo=json"


def request(query, params):

    search_path = search_string.format(
        endpoint=endpoint,
        query=urlencode({'q': query}),
        page=params['pageno'],
    )
    params['url'] = base_url + search_path
    params['raise_for_httperror'] = False
    return params


def response(resp):

    results = []
    json_data = resp.json()

    json_results = json_data.get('results')
    if not json_results:
        # when a search term has none results, loc sends a JSON in a HTTP 404
        # response and the HTTP status code is set in the 'status' element.
        if json_data.get('status') == 404:
            return results

    raise_for_httperror(resp)

    for result in json_results:

        url = result["item"].get("link")
        if not url:
            continue

        img_src = result['item'].get('service_medium')
        if not img_src or img_src == 'https://memory.loc.gov/pp/grp.gif':
            continue

        title = result['title']
        if title.startswith('['):
            title = title.strip('[]')

        content_items = [
            result['item'].get('created_published_date'),
            result['item'].get('summary', [None])[0],
            result['item'].get('notes', [None])[0],
            result['item'].get('part_of', [None])[0],
        ]

        author = None
        if result['item'].get('creators'):
            author = result['item']['creators'][0]['title']

        results.append(
            {
                'template': 'images.html',
                'url': url,
                'title': title,
                'content': ' / '.join([i for i in content_items if i]),
                'img_src': img_src,
                'thumbnail_src': result['item'].get('thumb_gallery'),
                'author': author,
            }
        )

    return results
