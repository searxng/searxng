# SPDX-License-Identifier: AGPL-3.0-or-later
"""Petalsearch Images

"""

from json import loads
from urllib.parse import urlencode
from datetime import datetime

from lxml import html

from searx.utils import extract_text

about = {
    "website": 'https://petalsearch.com/',
    "wikidata_id": 'Q104399280',
    "official_api_documentation": False,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ['images']
paging = True
time_range_support = False

safesearch = True
safesearch_table = {0: 'off', 1: 'moderate', 2: 'on'}

base_url = 'https://petalsearch.com/'
search_string = 'search?{query}&channel=image&ps=50&pn={page}&region={lang}&ss_mode={safesearch}&ss_type=normal'


def request(query, params):

    search_path = search_string.format(
        query=urlencode({'query': query}),
        page=params['pageno'],
        lang=params['language'].lower(),
        safesearch=safesearch_table[params['safesearch']],
    )

    params['url'] = base_url + search_path

    return params


def response(resp):
    results = []

    tree = html.fromstring(resp.text)
    root = tree.findall('.//script[3]')

    # Convert list to JSON
    json_content = extract_text(root)

    # Manipulate with JSON
    data = loads(json_content)

    for result in data['newImages']:
        url = result['url']
        title = result['title']
        thumbnail_src = result['image']

        pic_dict = result.get('extrainfo')

        date_from_api = pic_dict.get('publish_time')
        width = pic_dict.get('width')
        height = pic_dict.get('height')
        img_src = pic_dict.get('real_url')

        # Continue if img_src is missing
        if img_src is None or '':
            continue

        # Get and convert published date
        if date_from_api is not None:
            publishedDate = datetime.fromtimestamp(int(date_from_api))

        # Append results
        results.append(
            {
                'template': 'images.html',
                'url': url,
                'title': title,
                'img_src': img_src,
                'thumbnail_src': thumbnail_src,
                'width': width,
                'height': height,
                'publishedDate': publishedDate,
            }
        )

    return results
