# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""This is the implementation of the google images engine.

.. admonition:: Content-Security-Policy (CSP)

   This engine needs to allow images from the `data URLs`_ (prefixed with the
   ``data:`` scheme)::

       Header set Content-Security-Policy "img-src 'self' data: ;"

.. _data URLs:
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Data_URIs
"""

from urllib.parse import urlencode, unquote
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
    "results": 'HTML',
}

# engine dependent config
categories = ['images', 'web']
paging = False
use_locale_domain = True
time_range_support = True
safesearch = True

filter_mapping = {0: 'images', 1: 'active', 2: 'active'}


def scrap_out_thumbs(dom):
    """Scrap out thumbnail data from <script> tags."""
    ret_val = {}
    for script in eval_xpath(dom, '//script[contains(., "_setImgSrc(")]'):
        _script = script.text
        # _setImgSrc('0','data:image\/jpeg;base64,\/9j\/4AAQSkZJR ....');
        _thumb_no, _img_data = _script[len("_setImgSrc(") : -2].split(",", 1)
        _thumb_no = _thumb_no.replace("'", "")
        _img_data = _img_data.replace("'", "")
        _img_data = _img_data.replace(r"\/", r"/")
        ret_val[_thumb_no] = _img_data.replace(r"\x3d", "=")
    return ret_val


def scrap_img_by_id(script, data_id):
    """Get full image URL by data-id in parent element"""
    img_url = ''
    _script = script.split('\n')
    for i, line in enumerate(_script):
        if 'gstatic.com/images' in line and data_id in line and i + 1 < len(_script):
            url_line = _script[i + 1]
            img_url = url_line.split('"')[1]
            img_url = unquote(img_url.replace(r'\u00', r'%'))
    return img_url


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
                'tbm': "isch",
                **lang_info['params'],
                'ie': "utf8",
                'oe': "utf8",
                'num': 30,
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
    img_bas64_map = scrap_out_thumbs(dom)
    img_src_script = eval_xpath_getindex(dom, '//script[contains(., "AF_initDataCallback({key: ")]', 1).text

    # parse results
    #
    # root element::
    #     <div id="islmp" ..>
    # result div per image::
    #     <div jsmodel="tTXmib"> / <div jsaction="..." data-id="..."
    #     The data-id matches to a item in a json-data structure in::
    #         <script nonce="I+vqelcy/01CKiBJi5Z1Ow">AF_initDataCallback({key: 'ds:1', ... data:function(){return [ ...
    #     In this structure the link to the origin PNG, JPG or whatever is given
    # first link per image-div contains a <img> with the data-iid for bas64 encoded image data::
    #      <img class="rg_i Q4LuWd" data-iid="0"
    # second link per image-div is the target link::
    #      <a class="VFACy kGQAp" href="https://en.wikipedia.org/wiki/The_Sacrament_of_the_Last_Supper">
    # the second link also contains two div tags with the *description* and *publisher*::
    #      <div class="WGvvNb">The Sacrament of the Last Supper ...</div>
    #      <div class="fxgdke">en.wikipedia.org</div>

    root = eval_xpath(dom, '//div[@id="islmp"]')
    if not root:
        logger.error("did not find root element id='islmp'")
        return results

    root = root[0]
    for img_node in eval_xpath_list(root, './/img[contains(@class, "rg_i")]'):

        img_alt = eval_xpath_getindex(img_node, '@alt', 0)

        img_base64_id = eval_xpath(img_node, '@data-iid')
        if img_base64_id:
            img_base64_id = img_base64_id[0]
            thumbnail_src = img_bas64_map[img_base64_id]
        else:
            thumbnail_src = eval_xpath(img_node, '@src')
            if not thumbnail_src:
                thumbnail_src = eval_xpath(img_node, '@data-src')
            if thumbnail_src:
                thumbnail_src = thumbnail_src[0]
            else:
                thumbnail_src = ''

        link_node = eval_xpath_getindex(img_node, '../../../a[2]', 0)
        url = eval_xpath_getindex(link_node, '@href', 0, None)
        if url is None:
            logger.error("missing @href in node: %s", html.tostring(link_node))
            continue

        pub_nodes = eval_xpath(link_node, './div/div')
        pub_descr = img_alt
        pub_source = ''
        if pub_nodes:
            pub_descr = extract_text(pub_nodes[0])
            pub_source = extract_text(pub_nodes[1])

        img_src_id = eval_xpath_getindex(img_node, '../../../@data-id', 0)
        src_url = scrap_img_by_id(img_src_script, img_src_id)
        if not src_url:
            src_url = thumbnail_src

        results.append(
            {
                'url': url,
                'title': img_alt,
                'content': pub_descr,
                'source': pub_source,
                'img_src': src_url,
                # 'img_format': img_format,
                'thumbnail_src': thumbnail_src,
                'template': 'images.html',
            }
        )

    return results
