# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""This is the implementation of the Google Videos engine.

.. admonition:: Content-Security-Policy (CSP)

   This engine needs to allow images from the `data URLs`_ (prefixed with the
   ``data:`` scheme)::

     Header set Content-Security-Policy "img-src 'self' data: ;"

.. _data URLs:
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Data_URIs

"""

from typing import TYPE_CHECKING

from urllib.parse import urlencode
from lxml import html

from searx.utils import (
    eval_xpath,
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
)
from searx.enginelib.traits import EngineTraits

if TYPE_CHECKING:
    import logging

    logger: logging.Logger

traits: EngineTraits

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
language_support = True
time_range_support = True
safesearch = True


def request(query, params):
    """Google-Video search request"""

    google_info = get_google_info(params, traits)

    query_url = (
        'https://'
        + google_info['subdomain']
        + '/search'
        + "?"
        + urlencode(
            {
                'q': query,
                'tbm': "vid",
                'start': 10 * params['pageno'],
                **google_info['params'],
                'asearch': 'arc',
                'async': 'use_ac:true,_fmt:html',
            }
        )
    )

    if params['time_range'] in time_range_dict:
        query_url += '&' + urlencode({'tbs': 'qdr:' + time_range_dict[params['time_range']]})
    if params['safesearch']:
        query_url += '&' + urlencode({'safe': filter_mapping[params['safesearch']]})
    params['url'] = query_url

    params['cookies'] = google_info['cookies']
    params['headers'].update(google_info['headers'])
    return params


def response(resp):
    """Get response from google's search request"""
    results = []

    detect_google_sorry(resp)

    # convert the text to dom
    dom = html.fromstring(resp.text)

    # parse results
    for result in eval_xpath_list(dom, '//div[contains(@class, "g ")]'):

        img_src = eval_xpath_getindex(result, './/img/@src', 0, None)
        if img_src is None:
            continue

        title = extract_text(eval_xpath_getindex(result, './/a/h3[1]', 0))
        url = eval_xpath_getindex(result, './/a/h3[1]/../@href', 0)

        c_node = eval_xpath_getindex(result, './/div[@class="Uroaid"]', 0)
        content = extract_text(c_node)
        pub_info = extract_text(eval_xpath(result, './/div[@class="P7xzyf"]'))
        length = extract_text(eval_xpath(result, './/div[@class="J1mWY"]'))

        results.append(
            {
                'url': url,
                'title': title,
                'content': content,
                'author': pub_info,
                'thumbnail': img_src,
                'length': length,
                'template': 'videos.html',
            }
        )

    # parse suggestion
    for suggestion in eval_xpath_list(dom, suggestion_xpath):
        # append suggestion
        results.append({'suggestion': extract_text(suggestion)})

    return results
