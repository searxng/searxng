# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""DuckDuckGo Lite
"""

from json import loads

from lxml.html import fromstring

from searx.utils import (
    dict_subset,
    eval_xpath,
    eval_xpath_getindex,
    extract_text,
    match_language,
)
from searx.network import get

# about
about = {
    "website": 'https://lite.duckduckgo.com/lite',
    "wikidata_id": 'Q12805',
    "official_api_documentation": 'https://duckduckgo.com/api',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['general', 'web']
paging = True
supported_languages_url = 'https://duckduckgo.com/util/u588.js'
time_range_support = True

language_aliases = {
    'ar-SA': 'ar-XA',
    'es-419': 'es-XL',
    'ja': 'jp-JP',
    'ko': 'kr-KR',
    'sl-SI': 'sl-SL',
    'zh-TW': 'tzh-TW',
    'zh-HK': 'tzh-HK',
}

time_range_dict = {'day': 'd', 'week': 'w', 'month': 'm', 'year': 'y'}

# search-url
url = 'https://lite.duckduckgo.com/lite'
url_ping = 'https://duckduckgo.com/t/sl_l'

# match query's language to a region code that duckduckgo will accept
def get_region_code(lang, lang_list=None):
    if lang == 'all':
        return None

    lang_code = match_language(lang, lang_list or [], language_aliases, 'wt-WT')
    lang_parts = lang_code.split('-')

    # country code goes first
    return lang_parts[1].lower() + '-' + lang_parts[0].lower()


def request(query, params):

    params['url'] = url
    params['method'] = 'POST'

    params['data']['q'] = query

    # The API is not documented, so we do some reverse engineering and emulate
    # what https://lite.duckduckgo.com/lite/ does when you press "next Page"
    # link again and again ..

    params['headers']['Content-Type'] = 'application/x-www-form-urlencoded'

    # initial page does not have an offset
    if params['pageno'] == 2:
        # second page does have an offset of 30
        offset = (params['pageno'] - 1) * 30
        params['data']['s'] = offset
        params['data']['dc'] = offset + 1

    elif params['pageno'] > 2:
        # third and following pages do have an offset of 30 + n*50
        offset = 30 + (params['pageno'] - 2) * 50
        params['data']['s'] = offset
        params['data']['dc'] = offset + 1

    # initial page does not have additional data in the input form
    if params['pageno'] > 1:
        # request the second page (and more pages) needs 'o' and 'api' arguments
        params['data']['o'] = 'json'
        params['data']['api'] = 'd.js'

    # initial page does not have additional data in the input form
    if params['pageno'] > 2:
        # request the third page (and more pages) some more arguments
        params['data']['nextParams'] = ''
        params['data']['v'] = ''
        params['data']['vqd'] = ''

    region_code = get_region_code(params['language'], supported_languages)
    if region_code:
        params['data']['kl'] = region_code
        params['cookies']['kl'] = region_code

    params['data']['df'] = ''
    if params['time_range'] in time_range_dict:
        params['data']['df'] = time_range_dict[params['time_range']]
        params['cookies']['df'] = time_range_dict[params['time_range']]

    logger.debug("param data: %s", params['data'])
    logger.debug("param cookies: %s", params['cookies'])
    return params


# get response from search-request
def response(resp):

    headers_ping = dict_subset(resp.request.headers, ['User-Agent', 'Accept-Encoding', 'Accept', 'Cookie'])
    get(url_ping, headers=headers_ping)

    if resp.status_code == 303:
        return []

    results = []
    doc = fromstring(resp.text)

    result_table = eval_xpath(doc, '//html/body/form/div[@class="filters"]/table')
    if not len(result_table) >= 3:
        # no more results
        return []
    result_table = result_table[2]

    tr_rows = eval_xpath(result_table, './/tr')

    # In the last <tr> is the form of the 'previous/next page' links
    tr_rows = tr_rows[:-1]

    len_tr_rows = len(tr_rows)
    offset = 0

    while len_tr_rows >= offset + 4:

        # assemble table rows we need to scrap
        tr_title = tr_rows[offset]
        tr_content = tr_rows[offset + 1]
        offset += 4

        # ignore sponsored Adds <tr class="result-sponsored">
        if tr_content.get('class') == 'result-sponsored':
            continue

        a_tag = eval_xpath_getindex(tr_title, './/td//a[@class="result-link"]', 0, None)
        if a_tag is None:
            continue

        td_content = eval_xpath_getindex(tr_content, './/td[@class="result-snippet"]', 0, None)
        if td_content is None:
            continue

        results.append(
            {
                'title': a_tag.text_content(),
                'content': extract_text(td_content),
                'url': a_tag.get('href'),
            }
        )

    return results


# get supported languages from their site
def _fetch_supported_languages(resp):

    # response is a js file with regions as an embedded object
    response_page = resp.text
    response_page = response_page[response_page.find('regions:{') + 8 :]
    response_page = response_page[: response_page.find('}') + 1]

    regions_json = loads(response_page)
    supported_languages = map((lambda x: x[3:] + '-' + x[:2].upper()), regions_json.keys())

    return list(supported_languages)
