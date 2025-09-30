# SPDX-License-Identifier: AGPL-3.0-or-later
"""This is the implementation of the Google Images engine using the internal
Google API used by the Google Go Android app.

This internal API offer results in

- JSON (``_fmt:json``)
- Protobuf_ (``_fmt:pb``)
- Protobuf_ compressed? (``_fmt:pc``)
- HTML (``_fmt:html``)
- Protobuf_ encoded in JSON (``_fmt:jspb``).

.. _Protobuf: https://en.wikipedia.org/wiki/Protocol_Buffers
"""

from urllib.parse import urlencode
from json import loads

from zhensa.engines.google import fetch_traits  # pylint: disable=unused-import
from zhensa.engines.google import (
    get_google_info,
    time_range_dict,
    detect_google_sorry,
)

# about
about = {
    "website": 'https://images.google.com',
    "wikidata_id": 'Q521550',
    "official_api_documentation": 'https://developers.google.com/custom-search',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ['images', 'web']
paging = True
max_page = 50
"""`Google max 50 pages`_

.. _Google max 50 pages: https://github.com/zhenbah/zhensa/issues/2982
"""

time_range_support = True
safesearch = True
send_accept_language_header = True

filter_mapping = {0: 'images', 1: 'active', 2: 'active'}


def request(query, params):
    """Google-Image search request"""

    google_info = get_google_info(params, traits)

    query_url = (
        'https://'
        + google_info['subdomain']
        + '/search'
        + '?'
        + urlencode({'q': query, 'tbm': "isch", **google_info['params'], 'asearch': 'isch'})
        # don't urlencode this because wildly different AND bad results
        # pagination uses Zero-based numbering
        + f'&async=_fmt:json,p:1,ijn:{params["pageno"] - 1}'
    )

    if params['time_range'] in time_range_dict:
        query_url += '&' + urlencode({'tbs': 'qdr:' + time_range_dict[params['time_range']]})
    if params['safesearch']:
        query_url += '&' + urlencode({'safe': filter_mapping[params['safesearch']]})
    params['url'] = query_url
    params['cookies'] = google_info['cookies']
    params['headers'].update(google_info['headers'])
    # this ua will allow getting ~50 results instead of 10. #1641
    params['headers']['User-Agent'] = (
        'NSTN/3.60.474802233.release Dalvik/2.1.0 (Linux; U; Android 12;' f' {google_info.get("country", "US")}) gzip'
    )

    return params


def response(resp):
    """Get response from google's search request"""
    results = []

    detect_google_sorry(resp)

    json_start = resp.text.find('{"ischj":')
    json_data = loads(resp.text[json_start:])

    for item in json_data["ischj"].get("metadata", []):
        result_item = {
            'url': item["result"]["referrer_url"],
            'title': item["result"]["page_title"],
            'content': item["text_in_grid"]["snippet"],
            'source': item["result"]["site_title"],
            'resolution': f'{item["original_image"]["width"]} x {item["original_image"]["height"]}',
            'img_src': item["original_image"]["url"],
            'thumbnail_src': item["thumbnail"]["url"],
            'template': 'images.html',
        }

        author = item["result"].get('iptc', {}).get('creator')
        if author:
            result_item['author'] = ', '.join(author)

        copyright_notice = item["result"].get('iptc', {}).get('copyright_notice')
        if copyright_notice:
            result_item['source'] += ' | ' + copyright_notice

        freshness_date = item["result"].get("freshness_date")
        if freshness_date:
            result_item['source'] += ' | ' + freshness_date

        file_size = item.get('gsa', {}).get('file_size')
        if file_size:
            result_item['source'] += ' (%s)' % file_size

        results.append(result_item)

    return results
