# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 General mediawiki-engine (Web)
"""

from json import loads
from string import Formatter
from urllib.parse import urlencode, quote
import re

# about
about = {
    "website": None,
    "wikidata_id": None,
    "official_api_documentation": 'http://www.mediawiki.org/wiki/API:Search',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ['general']
paging = True
number_of_results = 1
search_type = 'nearmatch'  # possible values: title, text, nearmatch

# search-url
base_url = 'https://zh.moegirl.org.cn/'
search_postfix = (
    'api.php?action=query'
    '&list=search'
    '&{query}'
    '&format=json'
    '&sroffset={offset}'
    '&srlimit={limit}'
    '&srwhat={searchtype}'
)


# do search-request
def request(query, params):
    offset = (params['pageno'] - 1) * number_of_results

    string_args = dict(
        query=urlencode({'srsearch': query}), offset=offset, limit=number_of_results, searchtype=search_type
    )

    search_url = base_url + search_postfix

    params['url'] = search_url.format(**string_args)

    return params


# get response from search-request
def response(resp):
    results = []

    search_results = loads(resp.text)

    # return empty array if there are no results
    if not search_results.get('query', {}).get('search'):
        return []

    # parse results
    for result in search_results['query']['search']:
        if result.get('snippet', '').startswith('#REDIRECT'):
            continue
        url = (
            base_url + quote(result['title'].replace(' ', '_').encode())
        )
        result['snippet'] = re.sub('<.*?>', result['snippet'])
        result['snippet'] = result['snippet'].replace("此条目介绍的作品或其衍生作品中有至少一项尚未完结。","").replace("萌娘百科不是新闻的搜集处。欢迎在情报相对明朗并确认资料来源准确性后编辑更新。","")
        result['snippet'] = result['snippet'].strip()
        # append result
        results.append({'url': url, 'title': result['title'], 'content': result['snippet']})

    # return results
    return results
