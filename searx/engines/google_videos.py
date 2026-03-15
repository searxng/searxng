# SPDX-License-Identifier: AGPL-3.0-or-later
"""This is the implementation of the Google Videos engine.

.. admonition:: Content-Security-Policy (CSP)

   This engine needs to allow images from the `data URLs`_ (prefixed with the
   ``data:`` scheme)::

     Header set Content-Security-Policy "img-src 'self' data: ;"

.. _data URLs:
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Data_URIs
"""
import re
from urllib.parse import urlencode, urlparse, parse_qs, unquote
from lxml import html

from searx.utils import (
    eval_xpath_list,
    eval_xpath_getindex,
    extract_text,
)

from searx.engines.google import fetch_traits  # pylint: disable=unused-import
from searx.engines.google import (
    get_google_info,
    time_range_dict,
    filter_mapping,
    suggestion_xpath,
    detect_google_sorry,
    ui_async,
)
from searx.utils import get_embeded_stream_url

# about
about = {
    "website": 'https://www.google.com',
    "wikidata_id": 'Q219885',
    "official_api_documentation": 'https://developers.google.com/custom-search',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['videos', 'web']
paging = True
max_page = 50
language_support = True
time_range_support = True
safesearch = True


# =26;[3,"dimg_ZNMiZPCqE4apxc8P3a2tuAQ_137"]a87;data:image/jpeg;base64,/9j/4AAQSkZJRgABA
# ...6T+9Nl4cnD+gr9OK8I56/tX3l86nWYw//2Q==26;
RE_DATA_IMAGE = re.compile(r'"(dimg_[^"]*)"[^;]*;(data:image[^;]*;[^;]*);?')


def parse_data_images(text: str):
    data_image_map = {}

    for img_id, data_image in RE_DATA_IMAGE.findall(text):
        end_pos = data_image.rfind("=")
        if end_pos > 0:
            data_image = data_image[: end_pos + 1]
        data_image_map[img_id] = data_image
    logger.debug("data:image objects --> %s", list(data_image_map.keys()))
    return data_image_map


def request(query, params):
    """Google-Video search request"""
    google_info = get_google_info(params, traits)
    start = (params['pageno'] - 1) * 10

    query_url = (
        'https://'
        + google_info['subdomain']
        + '/search'
        + "?"
        + urlencode(
            {
                'q': query,
                'tbm': "vid",
                'start': start,
                **google_info['params'],
                'asearch': 'arc',
                'async': ui_async(start),
            }
        )
    )

    if params['time_range'] in time_range_dict:
        query_url += '&' + urlencode({'tbs': 'qdr:' + time_range_dict[params['time_range']]})
    if 'safesearch' in params:
        query_url += '&' + urlencode({'safe': filter_mapping[params['safesearch']]})
    params['url'] = query_url

    params['cookies'] = google_info['cookies']
    params['headers'].update(google_info['headers'])
    return params


def response(resp):
    """Get response from google's search request"""
    results = []

    detect_google_sorry(resp)
    data_image_map = parse_data_images(resp.text)

    # convert the text to dom
    dom = html.fromstring(resp.text)

    result_divs = eval_xpath_list(dom, '//div[contains(@class, "MjjYud")]')

    # parse results
    for result in result_divs:
        title = extract_text(
            eval_xpath_getindex(result, './/h3[contains(@class, "LC20lb")] | .//div[@role="heading"]', 0, default=None),
            allow_none=True,
        )
        url = eval_xpath_getindex(
            result, './/a[@jsname="UWckNb"]/@href | .//a[contains(@href, "/url?q=")]/@href', 0, default=None
        )
        if url and url.startswith('/url?q='):
            url = unquote(url[7:].split('&sa=U')[0])

        content = extract_text(
            eval_xpath_getindex(result, './/div[contains(@class, "ITZIwc")]', 0, default=None), allow_none=True
        )
        pub_info = extract_text(
            eval_xpath_getindex(
                result, './/div[contains(@class, "gqF9jc")] | .//div[contains(@class, "WRu9Cd")]', 0, default=None
            ),
            allow_none=True,
        )
        # Broader XPath to find any <img> element
        thumbnail = eval_xpath_getindex(result, './/img/@src', 0, default=None)
        duration = extract_text(
            eval_xpath_getindex(result, './/span[contains(@class, "k1U36b")]', 0, default=None), allow_none=True
        )
        video_id = eval_xpath_getindex(result, './/div[@jscontroller="rTuANe"]/@data-vid', 0, default=None)

        # Fallback for video_id from URL if not found via XPath
        if not video_id and url and 'youtube.com' in url:
            parsed_url = urlparse(url)
            video_id = parse_qs(parsed_url.query).get('v', [None])[0]

        # Handle thumbnail
        if thumbnail and thumbnail.startswith('data:image'):
            img_id = eval_xpath_getindex(result, './/img/@id', 0, default=None)
            if img_id and img_id in data_image_map:
                thumbnail = data_image_map[img_id]
            else:
                thumbnail = None
        if not thumbnail and video_id:
            thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

        # Handle video embed URL
        embed_url = None
        if video_id:
            embed_url = get_embeded_stream_url(f"https://www.youtube.com/watch?v={video_id}")
        elif url:
            embed_url = get_embeded_stream_url(url)

        # Only append results with valid title and url
        if title and url:
            results.append(
                {
                    'url': url,
                    'title': title,
                    'content': content or '',
                    'author': pub_info,
                    'thumbnail': thumbnail,
                    'length': duration,
                    'iframe_src': embed_url,
                    'template': 'videos.html',
                }
            )

    # parse suggestion
    for suggestion in eval_xpath_list(dom, suggestion_xpath):
        results.append({'suggestion': extract_text(suggestion)})

    return results
