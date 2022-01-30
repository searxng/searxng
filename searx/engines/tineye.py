# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""This engine implements *Tineye - reverse image search*

Using TinEye, you can search by image or perform what we call a reverse image
search.  You can do that by uploading an image or searching by URL. You can also
simply drag and drop your images to start your search.  TinEye constantly crawls
the web and adds images to its index.  Today, the TinEye index is over 50.2
billion images `[tineye.com] <https://tineye.com/how>`_.

.. hint::

   This SearXNG engine only supports *'searching by URL'* and it does not use
   the official API `[api.tineye.com] <https://api.tineye.com/python/docs/>`_.

"""

from urllib.parse import urlencode
from datetime import datetime

about = {
    "website": 'https://tineye.com',
    "wikidata_id": 'Q2382535',
    "official_api_documentation": 'https://api.tineye.com/python/docs/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

engine_type = 'online_url_search'
categories = ['general']
paging = True
safesearch = False
base_url = 'https://tineye.com'
search_string = '/result_json/?page={page}&{query}'


def request(query, params):

    if params['search_urls']['data:image']:
        query = params['search_urls']['data:image']
    elif params['search_urls']['http']:
        query = params['search_urls']['http']

    query = urlencode({'url': query})

    # see https://github.com/TinEye/pytineye/blob/main/pytineye/api.py
    params['url'] = base_url + search_string.format(query=query, page=params['pageno'])

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
    json_data = resp.json()
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
