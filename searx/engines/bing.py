# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Bing (Web)
"""

import re
from urllib.parse import urlencode
from lxml import html
from searx.utils import eval_xpath, extract_text, match_language

# about
about = {
    "website": 'https://www.bing.com',
    "wikidata_id": 'Q182496',
    "official_api_documentation": 'https://www.microsoft.com/en-us/bing/apis/bing-web-search-api',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['general']
paging = True
supported_languages_url = 'https://www.bing.com/account/general'
language_aliases = {'zh-CN': 'zh-CHS', 'zh-TW': 'zh-CHT', 'zh-HK': 'zh-CHT'}

# search-url
base_url = 'https://www.bing.com/'
search_string = 'search?{query}&first={offset}'


def _get_offset_from_pageno(pageno):
    return (pageno - 1) * 10 + 1


# do search-request
def request(query, params):
    offset = _get_offset_from_pageno(params.get('pageno', 0))

    if params['language'] == 'all':
        lang = 'EN'
    else:
        lang = match_language(params['language'], supported_languages, language_aliases)

    query = 'language:{} {}'.format(lang.split('-')[0].upper(), query)

    search_path = search_string.format(
        query=urlencode({'q': query}),
        offset=offset)

    params['url'] = base_url + search_path

    return params


# get response from search-request
def response(resp):
    results = []
    result_len = 0

    dom = html.fromstring(resp.text)
    # parse results
    for result in eval_xpath(dom, '//div[@class="sa_cc"]'):
        link = eval_xpath(result, './/h3/a')[0]
        url = link.attrib.get('href')
        title = extract_text(link)
        content = extract_text(eval_xpath(result, './/p'))

        # append result
        results.append({'url': url,
                        'title': title,
                        'content': content})

    # parse results again if nothing is found yet
    for result in eval_xpath(dom, '//li[@class="b_algo"]'):
        link = eval_xpath(result, './/h2/a')[0]
        url = link.attrib.get('href')
        title = extract_text(link)
        content = extract_text(eval_xpath(result, './/p'))

        # append result
        results.append({'url': url,
                        'title': title,
                        'content': content})

    try:
        result_len_container = "".join(eval_xpath(dom, '//span[@class="sb_count"]//text()'))
        if "-" in result_len_container:
            # Remove the part "from-to" for paginated request ...
            result_len_container = result_len_container[result_len_container.find("-") * 2 + 2:]

        result_len_container = re.sub('[^0-9]', '', result_len_container)
        if len(result_len_container) > 0:
            result_len = int(result_len_container)
    except Exception as e:
        logger.debug('result error :\n%s', e)

    if result_len and _get_offset_from_pageno(resp.search_params.get("pageno", 0)) > result_len:
        return []

    results.append({'number_of_results': result_len})
    return results


# get supported languages from their site
def _fetch_supported_languages(resp):
    lang_tags = set()

    setmkt = re.compile('setmkt=([^&]*)')
    dom = html.fromstring(resp.text)
    lang_links = eval_xpath(dom, "//li/a[contains(@href, 'setmkt')]")

    for a in lang_links:
        href = eval_xpath(a, './@href')[0]
        match = setmkt.search(href)
        l_tag = match.groups()[0]
        _lang, _nation = l_tag.split('-', 1)
        l_tag = _lang.lower() + '-' + _nation.upper()
        lang_tags.add(l_tag)

    return list(lang_tags)
