# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Google (Video)

For detailed description of the *REST-full* API see: `Query Parameter
Definitions`_.  Not all parameters can be appied.

.. _admonition:: Content-Security-Policy (CSP)

   This engine needs to allow images from the `data URLs`_ (prefixed with the
   ``data:` scheme).::

     Header set Content-Security-Policy "img-src 'self' data: ;"

.. _Query Parameter Definitions:
   https://developers.google.com/custom-search/docs/xml_results#WebSearch_Query_Parameter_Definitions
.. _data URLs:
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Data_URIs

"""

# pylint: disable=invalid-name, missing-function-docstring

import re
from urllib.parse import urlencode
from lxml import html

from searx import logger
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
    results_xpath,
    g_section_with_header,
    title_xpath,
    href_xpath,
    content_xpath,
    suggestion_xpath,
    spelling_suggestion_xpath,
    detect_google_sorry,
)

# pylint: disable=unused-import
from searx.engines.google import (
    supported_languages_url
    ,  _fetch_supported_languages
)
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

logger = logger.getChild('google video')

# engine dependent config

categories = ['videos']
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

def scrap_out_thumbs(dom):
    """Scrap out thumbnail data from <script> tags.
    """
    ret_val = dict()
    thumb_name = 'vidthumb'

    for script in eval_xpath_list(dom, '//script[contains(., "_setImagesSrc")]'):
        _script = script.text

        # var s='data:image/jpeg;base64, ...'
        _imgdata = _re("s='([^']*)").findall( _script)
        if not _imgdata:
            continue

        # var ii=['vidthumb4','vidthumb7']
        for _vidthumb in _re(r"(%s\d+)" % thumb_name).findall(_script):
            # At least the equal sign in the URL needs to be decoded
            ret_val[_vidthumb] = _imgdata[0].replace(r"\x3d", "=")

    # {google.ldidly=-1;google.ldi={"vidthumb8":"https://...
    for script in eval_xpath_list(dom, '//script[contains(., "google.ldi={")]'):
        _script = script.text
        for key_val in _re(r'"%s\d+\":\"[^\"]*"' % thumb_name).findall( _script) :
            match = _re(r'"(%s\d+)":"(.*)"' % thumb_name).search(key_val)
            if match:
                # At least the equal sign in the URL needs to be decoded
                ret_val[match.group(1)] = match.group(2).replace(r"\u003d", "=")

    logger.debug("found %s imgdata for: %s", thumb_name, ret_val.keys())
    return ret_val


def request(query, params):
    """Google-Video search request"""

    lang_info = get_lang_info(
        # pylint: disable=undefined-variable
        params, supported_languages, language_aliases, False
    )
    logger.debug(
        "HTTP header Accept-Language --> %s", lang_info['headers']['Accept-Language'])

    query_url = 'https://' + lang_info['subdomain'] + '/search' + "?" + urlencode({
        'q':   query,
        'tbm': "vid",
        **lang_info['params'],
        'ie': "utf8",
        'oe': "utf8",
    })

    if params['time_range'] in time_range_dict:
        query_url += '&' + urlencode({'tbs': 'qdr:' + time_range_dict[params['time_range']]})
    if params['safesearch']:
        query_url += '&' + urlencode({'safe': filter_mapping[params['safesearch']]})
    params['url'] = query_url

    params['headers'].update(lang_info['headers'])
    params['headers']['Accept'] = (
        'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        )
    return params


def response(resp):
    """Get response from google's search request"""
    results = []

    detect_google_sorry(resp)

    # convert the text to dom
    dom = html.fromstring(resp.text)
    vidthumb_imgdata = scrap_out_thumbs(dom)

    # parse results
    for result in eval_xpath_list(dom, results_xpath):

        # google *sections*
        if extract_text(eval_xpath(result, g_section_with_header)):
            logger.debug("ingoring <g-section-with-header>")
            continue

        title = extract_text(eval_xpath_getindex(result, title_xpath, 0))
        url = eval_xpath_getindex(result, href_xpath, 0)
        c_node = eval_xpath_getindex(result, content_xpath, 0)

        # <img id="vidthumb1" ...>
        img_id = eval_xpath_getindex(c_node, './div[1]//a/g-img/img/@id', 0, default=None)
        if img_id is None:
            continue
        img_src = vidthumb_imgdata.get(img_id, None)
        if not img_src:
            logger.error("no vidthumb imgdata for: %s" % img_id)
            img_src = eval_xpath_getindex(c_node, './div[1]//a/g-img/img/@src', 0)

        length = extract_text(eval_xpath(c_node, './/div[1]//a/div[3]'))
        content = extract_text(eval_xpath(c_node, './/div[2]/span'))
        pub_info = extract_text(eval_xpath(c_node, './/div[2]/div'))

        results.append({
            'url':         url,
            'title':       title,
            'content':     content,
            'length':      length,
            'author':      pub_info,
            'thumbnail':   img_src,
            'template':    'videos.html',
            })

    # parse suggestion
    for suggestion in eval_xpath_list(dom, suggestion_xpath):
        # append suggestion
        results.append({'suggestion': extract_text(suggestion)})

    for correction in eval_xpath_list(dom, spelling_suggestion_xpath):
        results.append({'correction': extract_text(correction)})

    return results
