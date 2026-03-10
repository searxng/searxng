# SPDX-License-Identifier: AGPL-3.0-or-later
"""This is the implementation of the Google Videos engine.

.. admonition:: Content-Security-Policy (CSP)

   This engine needs to allow images from the `data URLs`_ (prefixed with the
   ``data:`` scheme)::

     Header set Content-Security-Policy "img-src 'self' data: ;"

.. _data URLs:
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Data_URIs
"""

from urllib.parse import urlencode, urlparse, parse_qs, unquote, urlunparse
from lxml import html
import searx.network

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
    parse_data_images,
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


def request(query, params):
    """Google-Video search request"""
    google_info = get_google_info(params, traits)
    results_per_page = params.get('results_per_page', 10)

    # Google always returns ~10 results regardless of num.
    # The first request starts at the appropriate offset for the pageno.
    start = (params['pageno'] - 1) * results_per_page

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


def _parse_results(resp_text):
    """Helper to parse results from Google Videos HTML/Async response"""
    results = []
    data_image_map = parse_data_images(resp_text)
    dom = html.fromstring(resp_text)

    result_divs = eval_xpath_list(dom, '//div[contains(@class, "MjjYud")]')

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
        thumbnail = eval_xpath_getindex(result, './/img/@src', 0, default=None)
        duration = extract_text(
            eval_xpath_getindex(result, './/span[contains(@class, "k1U36b")]', 0, default=None), allow_none=True
        )
        video_id = eval_xpath_getindex(result, './/div[@jscontroller="rTuANe"]/@data-vid', 0, default=None)

        if not video_id and url and 'youtube.com' in url:
            parsed_url = urlparse(url)
            video_id = parse_qs(parsed_url.query).get('v', [None])[0]

        if thumbnail and thumbnail.startswith('data:image'):
            img_id = eval_xpath_getindex(result, './/img/@id', 0, default=None)
            if img_id and img_id in data_image_map:
                thumbnail = data_image_map[img_id]
            else:
                thumbnail = None
        if not thumbnail and video_id:
            thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

        embed_url = None
        if video_id:
            embed_url = get_embeded_stream_url(f"https://www.youtube.com/watch?v={video_id}")
        elif url:
            embed_url = get_embeded_stream_url(url)

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

    for suggestion in eval_xpath_list(dom, suggestion_xpath):
        results.append({'suggestion': extract_text(suggestion)})

    return results


def response(resp):
    """Get response from google's search request"""
    detect_google_sorry(resp)

    # Use the helper to parse the first page
    results = _parse_results(resp.text)

    search_params = resp.search_params
    results_per_page = search_params.get('results_per_page', 10)

    # Filter out suggestions to count only actual results for the goal
    actual_results_count = sum(1 for r in results if 'url' in r)

    # Adaptive multi-fetch if we need more results and the first page wasn't empty
    if results_per_page > 10 and actual_results_count > 0:
        parsed_url = urlparse(str(resp.url))
        query_params = parse_qs(parsed_url.query)

        current_start = int(query_params.get('start', [0])[0])
        # We fetch in blocks of 10. The max start index for this "page" is pageno * results_per_page - 10
        max_start = (search_params['pageno'] * results_per_page) - 10

        while sum(1 for r in results if 'url' in r) < results_per_page and current_start < max_start:
            current_start += 10
            query_params['start'] = [str(current_start)]
            # Keep async/asearch params if they were in the original request (master branch uses them)
            if 'async' in query_params:
                query_params['async'] = [ui_async(current_start)]

            new_url = urlunparse(parsed_url._replace(query=urlencode(query_params, doseq=True)))

            headers = search_params['headers'].copy()
            sub_resp = searx.network.get(
                new_url, headers=headers, cookies=search_params['cookies'], raise_for_httperror=False
            )

            if sub_resp.status_code != 200:
                break

            detect_google_sorry(sub_resp)
            new_results = _parse_results(sub_resp.text)
            new_actual_results = [r for r in new_results if 'url' in r]

            if not new_actual_results:
                break

            results.extend(new_results)

    return results
