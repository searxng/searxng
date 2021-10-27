# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Tineye - Reverse search images

"""

from json import loads
from urllib.parse import urlencode
from datetime import datetime

about = {
    "website": 'https://tineye.com',
    "wikidata_id": 'Q2382535',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ['images']
paging = True
safesearch = False
base_url = 'https://tineye.com'
search_string = '/result_json/?page={page}&{query}'


def request(query, params):
    # see https://github.com/TinEye/pytineye/blob/main/pytineye/api.py
    params['url'] = base_url + search_string.format(query=urlencode({'url': query}), page=params['pageno'])

    params['headers'].update(
        {
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, defalte, br',
            'Host': 'tineye.com',
            'DNT': '1',
            'TE': 'trailers',
        }
    )
    return params


def response(resp):
    results = []

    # Define wanted results
    json_data = loads(resp.text)
    number_of_results = json_data['num_matches']

    for i in json_data['matches']:
        image_format = i['format']
        width = i['width']
        height = i['height']
        thumbnail_src = i['image_url']
        backlink = i['domains'][0]['backlinks'][0]
        url = backlink['backlink']
        source = backlink['url']
        title = backlink['image_name']
        img_src = backlink['url']

        # Get and convert published date
        api_date = backlink['crawl_date'][:-3]
        publishedDate = datetime.fromisoformat(api_date)

        # Append results
        results.append(
            {
                'template': 'images.html',
                'url': url,
                'thumbnail_src': thumbnail_src,
                'source': source,
                'title': title,
                'img_src': img_src,
                'format': image_format,
                'widht': width,
                'height': height,
                'publishedDate': publishedDate,
            }
        )

    # Append number of results
    results.append({'number_of_results': number_of_results})

    return results
