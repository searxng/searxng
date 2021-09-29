# SPDX-License-Identifier: AGPL-3.0-or-later
"""

 Library of Congress : images from Prints and Photographs Online Catalog

"""

from json import loads
from urllib.parse import urlencode


about = {
    "website": 'https://www.loc.gov/pictures/',
    "wikidata_id": 'Q131454',
    "official_api_documentation": 'https://www.loc.gov/pictures/api',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ['images']

paging = True

base_url = 'https://loc.gov/pictures/search/?'
search_string = "&sp={page}&{query}&fo=json"

IMG_SRC_FIXES = {
    'https://tile.loc.gov/storage-services/': 'https://tile.loc.gov/storage-services/',
    'https://loc.gov/pictures/static/images/': 'https://tile.loc.gov/storage-services/',
    'https://www.loc.gov/pictures/cdn/': 'https://tile.loc.gov/storage-services/',
}


def request(query, params):

    search_path = search_string.format(
        query=urlencode({'q': query}),
        page=params['pageno'])

    params['url'] = base_url + search_path

    return params


def response(resp):
    results = []

    json_data = loads(resp.text)

    for result in json_data['results']:
        img_src = result['image']['full']
        for url_prefix, url_replace in IMG_SRC_FIXES.items():
            if img_src.startswith(url_prefix):
                img_src = img_src.replace(url_prefix, url_replace)
                break
        else:
            img_src = result['image']['thumb']
        results.append({
            'url': result['links']['item'],
            'title': result['title'],
            'img_src': img_src,
            'thumbnail_src': result['image']['thumb'],
            'author': result['creator'],
            'template': 'images.html'
        })

    return results
