# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""This is the implementation of the google videos engine.

.. admonition:: Content-Security-Policy (CSP)

   This engine needs to allow images from the `data URLs`_ (prefixed with the
   ``data:`` scheme)::

     Header set Content-Security-Policy "img-src 'self' data: ;"

.. _data URLs:
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Data_URIs

"""

# pylint: disable=invalid-name

import re
from urllib.parse import urlencode
from lxml import html

from searx.utils import (
    eval_xpath,
    eval_xpath_list,
    eval_xpath_getindex,
    extract_text,
)

from searx.engines.google import (
    get_lang_info,
    time_range_dict,
    filter_mapping,
    g_section_with_header,
    title_xpath,
    suggestion_xpath,
    detect_google_sorry,
)

# pylint: disable=unused-import
from searx.engines.google import supported_languages_url, _fetch_supported_languages

# pylint: enable=unused-import

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
paging = False
language_support = True
use_locale_domain = True
time_range_support = True
safesearch = True

RE_CACHE = {}


def _re(regexpr):
    """returns compiled regular expression"""
    RE_CACHE[regexpr] = RE_CACHE.get(regexpr, re.compile(regexpr))
    return RE_CACHE[regexpr]


def scrap_out_thumbs_src(dom):
    ret_val = {}
    thumb_name = 'dimg_'
    for script in eval_xpath_list(dom, '//script[contains(., "google.ldi={")]'):
        _script = script.text
        # "dimg_35":"https://i.ytimg.c....",
        _dimurl = _re("s='([^']*)").findall(_script)
        for k, v in _re('(' + thumb_name + '[0-9]*)":"(http[^"]*)').findall(_script):
            v = v.replace(r'\u003d', '=')
            v = v.replace(r'\u0026', '&')
            ret_val[k] = v
    logger.debug("found %s imgdata for: %s", thumb_name, ret_val.keys())
    return ret_val


def scrap_out_thumbs(dom):
    """Scrap out thumbnail data from <script> tags."""
    ret_val = {}
    thumb_name = 'dimg_'

    for script in eval_xpath_list(dom, '//script[contains(., "_setImagesSrc")]'):
        _script = script.text

        # var s='data:image/jpeg;base64, ...'
        _imgdata = _re("s='([^']*)").findall(_script)
        if not _imgdata:
            continue

        # var ii=['dimg_17']
        for _vidthumb in _re(r"(%s\d+)" % thumb_name).findall(_script):
            # At least the equal sign in the URL needs to be decoded
            ret_val[_vidthumb] = _imgdata[0].replace(r"\x3d", "=")

    logger.debug("found %s imgdata for: %s", thumb_name, ret_val.keys())
    return ret_val


def request(query, params):
    """Google-Video search request"""

    lang_info = get_lang_info(params, supported_languages, language_aliases, False)
    logger.debug("HTTP header Accept-Language --> %s", lang_info['headers']['Accept-Language'])

    query_url = (
        'https://'
        + lang_info['subdomain']
        + '/search'
        + "?"
        + urlencode(
            {
                'q': query,
                'tbm': "vid",
                **lang_info['params'],
                'ie': "utf8",
                'oe': "utf8",
            }
        )
    )

    if params['time_range'] in time_range_dict:
        query_url += '&' + urlencode({'tbs': 'qdr:' + time_range_dict[params['time_range']]})
    if params['safesearch']:
        query_url += '&' + urlencode({'safe': filter_mapping[params['safesearch']]})
    params['url'] = query_url

    params['headers'].update(lang_info['headers'])
    params['headers']['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    return params


def response(resp):
    """Get response from google's search request"""
    results = []

    detect_google_sorry(resp)

    # convert the text to dom
    dom = html.fromstring(resp.text)
    vidthumb_imgdata = scrap_out_thumbs(dom)
    thumbs_src = scrap_out_thumbs_src(dom)
    logger.debug(str(thumbs_src))

    # parse results
    for result in eval_xpath_list(dom, '//div[contains(@class, "g ")]'):

        # ignore google *sections*
        if extract_text(eval_xpath(result, g_section_with_header)):
            logger.debug("ingoring <g-section-with-header>")
            continue

        # ingnore articles without an image id / e.g. news articles
        img_id = eval_xpath_getindex(result, './/g-img/img/@id', 0, default=None)
        if img_id is None:
            logger.error("no img_id found in item %s (news article?)", len(results) + 1)
            continue

        img_src = vidthumb_imgdata.get(img_id, None)
        if not img_src:
            img_src = thumbs_src.get(img_id, "")

        title = extract_text(eval_xpath_getindex(result, title_xpath, 0))
        url = eval_xpath_getindex(result, './/div[@class="dXiKIc"]//a/@href', 0)
        length = extract_text(eval_xpath(result, './/div[contains(@class, "P7xzyf")]/span/span'))
        c_node = eval_xpath_getindex(result, './/div[@class="Uroaid"]', 0)
        content = extract_text(c_node)
        pub_info = extract_text(eval_xpath(result, './/div[@class="Zg1NU"]'))

        results.append(
            {
                'url': url,
                'title': title,
                'content': content,
                'length': length,
                'author': pub_info,
                'thumbnail': img_src,
                'template': 'videos.html',
            }
        )

    # parse suggestion
    for suggestion in eval_xpath_list(dom, suggestion_xpath):
        # append suggestion
        results.append({'suggestion': extract_text(suggestion)})

    return results
