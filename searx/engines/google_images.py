# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""This is the implementation of the google images engine using the google internal API used the Google Go Android app.
This internal API offer results in
- JSON (_fmt:json)
- Protobuf (_fmt:pb)
- Protobuf compressed? (_fmt:pc)
- HTML (_fmt:html)
- Protobuf encoded in JSON (_fmt:jspb).

.. admonition:: Content-Security-Policy (CSP)

   This engine needs to allow images from the `data URLs`_ (prefixed with the
   ``data:`` scheme)::

       Header set Content-Security-Policy "img-src 'self' data: ;"

.. _data URLs:
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Data_URIs
"""

from urllib.parse import urlencode
from json import loads

from searx.engines.google import (
    get_lang_info,
    time_range_dict,
    detect_google_sorry,
)

# pylint: disable=unused-import
from searx.engines.google import supported_languages_url, _fetch_supported_languages

# pylint: enable=unused-import

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
use_locale_domain = True
time_range_support = True
safesearch = True
send_accept_language_header = True

filter_mapping = {0: 'images', 1: 'active', 2: 'active'}


def request(query, params):
    """Google-Image search request"""

    lang_info = get_lang_info(params, supported_languages, language_aliases, False)

    query_url = (
        'https://'
        + lang_info['subdomain']
        + '/search'
        + "?"
        + urlencode(
            {
                'q': query,
                'tbm': "isch",
                **lang_info['params'],
                'ie': "utf8",
                'oe': "utf8",
                'asearch': 'isch',
                'async': '_fmt:json,p:1,ijn:' + str(params['pageno']),
            }
        )
    )

    if params['time_range'] in time_range_dict:
        query_url += '&' + urlencode({'tbs': 'qdr:' + time_range_dict[params['time_range']]})
    if params['safesearch']:
        query_url += '&' + urlencode({'safe': filter_mapping[params['safesearch']]})
    params['url'] = query_url

    params['headers'].update(lang_info['headers'])
    params['headers']['User-Agent'] = 'NSTN/3.60.474802233.release Dalvik/2.1.0 (Linux; U; Android 12; US) gzip'
    params['headers']['Accept'] = '*/*'
    return params


def response(resp):
    """Get response from google's search request"""
    results = []

    detect_google_sorry(resp)

    response_2nd_line = resp.text.split("\n", 1)[1]
    json_data = loads(response_2nd_line)["ischj"]

    for item in json_data["metadata"]:
        results.append(
            {
                'url': item["result"]["referrer_url"],
                'title': item["result"]["page_title"],
                'content': item["text_in_grid"]["snippet"],
                'source': item["result"]["site_title"],
                'format': f'{item["original_image"]["width"]} x item["original_image"]["height"]',
                'img_src': item["original_image"]["url"],
                'thumbnail_src': item["thumbnail"]["url"],
                'template': 'images.html',
            }
        )

    return results
