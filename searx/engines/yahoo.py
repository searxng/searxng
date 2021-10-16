# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Yahoo (Web)

"""

from urllib.parse import unquote, urlencode
from lxml import html
from searx.utils import extract_text, extract_url, match_language, eval_xpath

# about
about = {
    "website": 'https://search.yahoo.com/',
    "wikidata_id": None,
    "official_api_documentation": 'https://developer.yahoo.com/api/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['general']
paging = True
time_range_support = True

# search-url
base_url = 'https://search.yahoo.com/'
search_url = 'search?{query}&b={offset}&fl=1&vl=lang_{lang}'
search_url_with_time = 'search?{query}&b={offset}&fl=1&vl=lang_{lang}&age={age}&btf={btf}&fr2=time'

supported_languages_url = 'https://search.yahoo.com/web/advanced'

# specific xpath variables
results_xpath = "//div[contains(concat(' ', normalize-space(@class), ' '), ' Sr ')]"
url_xpath = './/h3/a/@href'
title_xpath = './/h3/a'
content_xpath = './/div[contains(@class, "compText")]'
suggestion_xpath = "//div[contains(concat(' ', normalize-space(@class), ' '), ' AlsoTry ')]//a"

time_range_dict = {
    'day': ['1d', 'd'],
    'week': ['1w', 'w'],
    'month': ['1m', 'm']
}

language_aliases = {
    'zh-CN': 'zh-CHS',
    'zh-TW': 'zh-CHT',
    'zh-HK': 'zh-CHT'
}

# remove yahoo-specific tracking-url
def parse_url(url_string):
    endings = ['/RS', '/RK']
    endpositions = []
    start = url_string.find('http', url_string.find('/RU=') + 1)

    for ending in endings:
        endpos = url_string.rfind(ending)
        if endpos > -1:
            endpositions.append(endpos)

    if start == 0 or len(endpositions) == 0:
        return url_string

    end = min(endpositions)
    return unquote(url_string[start:end])

def _get_url(query, offset, language, time_range):
    if time_range in time_range_dict:
        return base_url + search_url_with_time.format(
            offset = offset,
            query = urlencode({'p': query}),
            lang = language,
            age = time_range_dict[time_range][0],
            btf = time_range_dict[time_range][1]
        )
    return base_url + search_url.format(
        offset=offset,
        query=urlencode({'p': query}),
        lang=language
    )

def _get_language(params):
    if params['language'] == 'all':
        return 'en'

    language = match_language(params['language'], supported_languages, language_aliases)
    if language not in language_aliases.values():
        language = language.split('-')[0]
    language = language.replace('-', '_').lower()

    return language


# do search-request
def request(query, params):
    if params['time_range'] and params['time_range'] not in time_range_dict:
        return params

    offset = (params['pageno'] - 1) * 10 + 1
    language = _get_language(params)

    params['url'] = _get_url(query, offset, language, params['time_range'])

    return params


# get response from search-request
def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    try:
        results_num = int(
            eval_xpath(
                dom,
                '//div[@class="compPagination"]/span[last()]/text()'
            )[0].split()[0].replace(',', '')
        )
        results.append({'number_of_results': results_num})
    except:  # pylint: disable=bare-except
        pass

    # parse results
    for result in eval_xpath(dom, results_xpath):
        try:
            url = parse_url(extract_url(eval_xpath(result, url_xpath), search_url))
            title = extract_text(eval_xpath(result, title_xpath)[0])

        except:  # pylint: disable=bare-except
            continue

        content = extract_text(eval_xpath(result, content_xpath)[0])

        # append result
        results.append({
            'url': url,
            'title': title,
            'content': content
        })

    # if no suggestion found, return results
    suggestions = eval_xpath(dom, suggestion_xpath)
    if not suggestions:
        return results

    # parse suggestion
    for suggestion in suggestions:
        # append suggestion
        results.append({'suggestion': extract_text(suggestion)})

    # return results
    return results


# get supported languages from their site
def _fetch_supported_languages(resp):
    supported_languages = []
    dom = html.fromstring(resp.text)
    options = eval_xpath(dom, '//div[@id="yschlang"]/span/label/input')
    for option in options:
        code_parts = eval_xpath(option, './@value')[0][5:].split('_')
        if len(code_parts) == 2:
            code = code_parts[0] + '-' + code_parts[1].upper()
        else:
            code = code_parts[0]
        supported_languages.append(code)

    return supported_languages
