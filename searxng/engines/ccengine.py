# SPDX-License-Identifier: AGPL-3.0-or-later
"""

 Creative Commons search engine (Images)

"""

from json import loads
from urllib.parse import urlencode


about = {
    "website": 'https://search.creativecommons.org/',
    "wikidata_id": None,
    "official_api_documentation": 'https://api.creativecommons.engineering/v1/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ['images']

paging = True
nb_per_page = 20

base_url = 'https://api.creativecommons.engineering/v1/images?'
search_string = '&page={page}&page_size={nb_per_page}&format=json&{query}'


def request(query, params):

    search_path = search_string.format(
        query=urlencode({'q': query}),
        nb_per_page=nb_per_page,
        page=params['pageno'])

    params['url'] = base_url + search_path

    return params


def response(resp):
    results = []

    json_data = loads(resp.text)

    for result in json_data['results']:
        results.append({'url': result['foreign_landing_url'],
                        'title': result['title'],
                        'img_src': result['url'],
                        'template': 'images.html'})

    return results
