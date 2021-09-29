# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 General mediawiki-engine (Web)
"""

from json import loads
from string import Formatter
from urllib.parse import urlencode, quote

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
base_url = 'https://{language}.wikipedia.org/'
search_postfix = 'w/api.php?action=query'\
    '&list=search'\
    '&{query}'\
    '&format=json'\
    '&sroffset={offset}'\
    '&srlimit={limit}'\
    '&srwhat={searchtype}'


# do search-request
def request(query, params):
    offset = (params['pageno'] - 1) * number_of_results

    string_args = dict(query=urlencode({'srsearch': query}),
                       offset=offset,
                       limit=number_of_results,
                       searchtype=search_type)

    format_strings = list(Formatter().parse(base_url))

    if params['language'] == 'all':
        language = 'en'
    else:
        language = params['language'].split('-')[0]

    # format_string [('https://', 'language', '', None), ('.wikipedia.org/', None, None, None)]
    if any(x[1] == 'language' for x in format_strings):
        string_args['language'] = language

    # write search-language back to params, required in response
    params['language'] = language

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
        url = base_url.format(language=resp.search_params['language']) +\
            'wiki/' + quote(result['title'].replace(' ', '_').encode())

        # append result
        results.append({'url': url,
                        'title': result['title'],
                        'content': ''})

    # return results
    return results
