# SPDX-License-Identifier: AGPL-3.0-or-later
"""Searchcode (IT)

"""

from json import loads
from urllib.parse import urlencode

# about
about = {
    "website": 'https://searchcode.com/',
    "wikidata_id": None,
    "official_api_documentation": 'https://searchcode.com/api/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ['it']
search_api = 'https://searchcode.com/api/codesearch_I/?'

# special code-endings which are not recognised by the file ending
code_endings = {'cs': 'c#', 'h': 'c', 'hpp': 'cpp', 'cxx': 'cpp'}

# paging is broken in searchcode.com's API .. not sure it will ever been fixed
# paging = True


def request(query, params):
    args = urlencode(
        {
            'q': query,
            # paging is broken in searchcode.com's API
            # 'p': params['pageno'] - 1,
            # 'per_page': 10,
        }
    )
    params['url'] = search_api + args
    logger.debug("query_url --> %s", params['url'])
    return params


def response(resp):
    results = []

    search_results = loads(resp.text)

    # parse results
    for result in search_results.get('results', []):
        href = result['url']
        title = "" + result['name'] + " - " + result['filename']
        repo = result['repo']

        lines = {}
        for line, code in result['lines'].items():
            lines[int(line)] = code

        code_language = code_endings.get(
            result['filename'].split('.')[-1].lower(), result['filename'].split('.')[-1].lower()
        )

        # append result
        results.append(
            {
                'url': href,
                'title': title,
                'content': '',
                'repository': repo,
                'codelines': sorted(lines.items()),
                'code_language': code_language,
                'template': 'code.html',
            }
        )

    # return results
    return results
