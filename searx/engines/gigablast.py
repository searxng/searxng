# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""
 Gigablast (Web)
"""
# pylint: disable=invalid-name

import re
from time import time
from json import loads
from urllib.parse import urlencode
from searx.network import get

# about
about = {
    "website": 'https://www.gigablast.com',
    "wikidata_id": 'Q3105449',
    "official_api_documentation": 'https://gigablast.com/api.html',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ['general', 'web']
# gigablast's pagination is totally damaged, don't use it
paging = False
safesearch = True

# search-url
base_url = 'https://gigablast.com'
search_path = '/search?'

# ugly hack: gigablast requires a random extra parameter which can be extracted
# from the source code of the gigablast HTTP client
extra_param = ''
# timestamp of the last fetch of extra_param
extra_param_ts = 0
# after how many seconds extra_param expire
extra_param_expiration_delay = 3000


def fetch_extra_param(query_args, headers):

    # example:
    #
    # var uxrl='/search?c=main&qlangcountry=en-us&q=south&s=10&rand=1590740241635&n';
    # uxrl=uxrl+'sab=730863287';
    #
    # extra_param --> "rand=1590740241635&nsab=730863287"

    global extra_param, extra_param_ts  # pylint: disable=global-statement

    extra_param_ts = time()
    extra_param_path = search_path + urlencode(query_args)
    text = get(base_url + extra_param_path, headers=headers).text

    re_var = None
    for line in text.splitlines():
        if re_var is None and extra_param_path in line:
            var = line.split("=")[0].split()[1]  # e.g. var --> 'uxrl'
            re_var = re.compile(var + "\\s*=\\s*" + var + "\\s*\\+\\s*'" + "(.*)" + "'(.*)")
            extra_param = line.split("'")[1][len(extra_param_path) :]
            continue
        if re_var is not None and re_var.search(line):
            extra_param += re_var.search(line).group(1)
            break


# do search-request
def request(query, params):  # pylint: disable=unused-argument
    query_args = dict(c='main', q=query, dr=1, showgoodimages=0)

    if params['language'] and params['language'] != 'all':
        query_args['qlangcountry'] = params['language']
        query_args['qlang'] = params['language'].split('-')[0]

    if params['safesearch'] >= 1:
        query_args['ff'] = 1

    # see API http://www.gigablast.com/api.html#/search
    # Take into account, that the API has some quirks ..
    if time() > (extra_param_ts + extra_param_expiration_delay):
        fetch_extra_param(query_args, params['headers'])

    query_args['format'] = 'json'
    params['url'] = base_url + search_path + urlencode(query_args) + extra_param

    return params


# get response from search-request
def response(resp):
    results = []

    response_json = loads(resp.text)

    # logger.debug('gigablast returns %s results', len(response_json['results']))

    for result in response_json['results']:
        # see "Example JSON Output (&format=json)"
        # at http://www.gigablast.com/api.html#/search

        # sort out meaningless result

        title = result.get('title')
        if len(title) < 2:
            continue

        url = result.get('url')
        if len(url) < 9:
            continue

        content = result.get('sum')
        if len(content) < 5:
            continue

        # extend fields

        subtitle = result.get('title')
        if len(subtitle) > 3 and subtitle != title:
            title += " - " + subtitle

        results.append(dict(url=url, title=title, content=content))

    return results
