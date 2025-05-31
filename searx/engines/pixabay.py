# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pixabay provides royalty-free media (images, videos)"""

from datetime import timedelta
from urllib.parse import quote_plus, urlencode
from dateutil import parser
from searx.utils import gen_useragent

# about
about = {
    "website": 'https://pixabay.com',
    "wikidata_id": 'Q1746538',
    "official_api_documentation": 'https://pixabay.com/api/docs/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

base_url = 'https://pixabay.com'
categories = ['images']
pixabay_type = "images"  # alternative: 'videos'

paging = True
safesearch = True
time_range_support = True

safesearch_map = {0: 'off', 1: '1', 2: '1'}
time_range_map = {'day': '1d', 'week': '1w', 'month': '1m', 'year': '1y'}

# using http2 returns forbidden errors
enable_http2 = False


def request(query, params):
    args = {
        'pagi': params['pageno'],
    }
    if params['time_range']:
        args['date'] = time_range_map[params['time_range']]

    params['url'] = f"{base_url}/{pixabay_type}/search/{quote_plus(query)}/?{urlencode(args)}"
    params['headers'] = {
        'User-Agent': gen_useragent() + " Pixabay",
        'Accept': 'application/json',
        'x-bootstrap-cache-miss': '1',
        'x-fetch-bootstrap': '1',
    }
    params['cookies']['g_rated'] = safesearch_map[params['safesearch']]

    # prevent automatic redirects to first page on pagination
    params['allow_redirects'] = False

    return params


def _image_result(result):
    return {
        'template': 'images.html',
        'url': base_url + result["href"],
        # images are sorted in ascending quality
        'thumbnail_src': list(result['sources'].values())[0],
        'img_src': list(result['sources'].values())[-1],
        'title': result.get('name'),
        'content': result.get('description', ''),
    }


def _video_result(result):
    return {
        'template': 'videos.html',
        'url': base_url + result["href"],
        # images are sorted in ascending quality
        'thumbnail': result['sources'].get('thumbnail'),
        'iframe_src': result['sources'].get('embed'),
        'title': result.get('name'),
        'content': result.get('description', ''),
        'length': timedelta(seconds=result['duration']),
        'publishedDate': parser.parse(result['uploadDate']),
    }


def response(resp):
    results = []

    # if there are no results on this page, we get a redirect
    # to the first page
    if resp.status_code == 302:
        return results

    json_data = resp.json()

    for result in json_data.get('page', {}).get('results', []):
        if result['mediaType'] in ('photo', 'illustration', 'vector'):
            results.append(_image_result(result))
        elif result['mediaType'] == 'video':
            results.append(_video_result(result))

    return results
