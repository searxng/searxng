# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Wikipedia (Web)
"""

from urllib.parse import quote
from json import loads
from lxml.html import fromstring
from searx.utils import match_language, searx_useragent
from searx.network import raise_for_httperror

# about
about = {
    "website": 'https://www.wikipedia.org/',
    "wikidata_id": 'Q52',
    "official_api_documentation": 'https://en.wikipedia.org/api/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# search-url
search_url = 'https://{language}.wikipedia.org/api/rest_v1/page/summary/{title}'
supported_languages_url = 'https://meta.wikimedia.org/wiki/List_of_Wikipedias'
language_variants = {"zh": ("zh-cn", "zh-hk", "zh-mo", "zh-my", "zh-sg", "zh-tw")}


# set language in base_url
def url_lang(lang):
    lang_pre = lang.split('-')[0]
    if lang_pre == 'all' or lang_pre not in supported_languages and lang_pre not in language_aliases:
        return 'en'
    return match_language(lang, supported_languages, language_aliases).split('-')[0]


# do search-request
def request(query, params):
    if query.islower():
        query = query.title()

    language = url_lang(params['language'])
    params['url'] = search_url.format(title=quote(query), language=language)

    if params['language'].lower() in language_variants.get(language, []):
        params['headers']['Accept-Language'] = params['language'].lower()

    params['headers']['User-Agent'] = searx_useragent()
    params['raise_for_httperror'] = False
    params['soft_max_redirects'] = 2

    return params


# get response from search-request
def response(resp):
    if resp.status_code == 404:
        return []

    if resp.status_code == 400:
        try:
            api_result = loads(resp.text)
        except:
            pass
        else:
            if (
                api_result['type'] == 'https://mediawiki.org/wiki/HyperSwitch/errors/bad_request'
                and api_result['detail'] == 'title-invalid-characters'
            ):
                return []

    raise_for_httperror(resp)

    results = []
    api_result = loads(resp.text)

    # skip disambiguation pages
    if api_result.get('type') != 'standard':
        return []

    title = api_result['title']
    wikipedia_link = api_result['content_urls']['desktop']['page']

    results.append({'url': wikipedia_link, 'title': title})

    results.append(
        {
            'infobox': title,
            'id': wikipedia_link,
            'content': api_result.get('extract', ''),
            'img_src': api_result.get('thumbnail', {}).get('source'),
            'urls': [{'title': 'Wikipedia', 'url': wikipedia_link}],
        }
    )

    return results


# get supported languages from their site
def _fetch_supported_languages(resp):
    supported_languages = {}
    dom = fromstring(resp.text)
    tables = dom.xpath('//table[contains(@class,"sortable")]')
    for table in tables:
        # exclude header row
        trs = table.xpath('.//tr')[1:]
        for tr in trs:
            td = tr.xpath('./td')
            code = td[3].xpath('./a')[0].text
            name = td[2].xpath('./a')[0].text
            english_name = td[1].xpath('./a')[0].text
            articles = int(td[4].xpath('./a/b')[0].text.replace(',', ''))
            # exclude languages with too few articles
            if articles >= 100:
                supported_languages[code] = {"name": name, "english_name": english_name}

    return supported_languages
