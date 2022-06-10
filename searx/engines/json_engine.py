# SPDX-License-Identifier: AGPL-3.0-or-later

from collections.abc import Iterable
from json import loads
from urllib.parse import urlencode
from searx.utils import to_string, html_to_text


search_url = None
url_query = None
content_query = None
title_query = None
content_html_to_text = False
title_html_to_text = False
paging = False
suggestion_query = ''
results_query = ''

cookies = {}
headers = {}
'''Some engines might offer different result based on cookies or headers.
Possible use-case: To set safesearch cookie or header to moderate.'''

# parameters for engines with paging support
#
# number of results on each page
# (only needed if the site requires not a page number, but an offset)
page_size = 1
# number of the first page (usually 0 or 1)
first_page_num = 1


def iterate(iterable):
    if type(iterable) == dict:
        it = iterable.items()

    else:
        it = enumerate(iterable)
    for index, value in it:
        yield str(index), value


def is_iterable(obj):
    if type(obj) == str:
        return False
    return isinstance(obj, Iterable)


def parse(query):
    q = []
    for part in query.split('/'):
        if part == '':
            continue
        else:
            q.append(part)
    return q


def do_query(data, q):
    ret = []
    if not q:
        return ret

    qkey = q[0]

    for key, value in iterate(data):

        if len(q) == 1:
            if key == qkey:
                ret.append(value)
            elif is_iterable(value):
                ret.extend(do_query(value, q))
        else:
            if not is_iterable(value):
                continue
            if key == qkey:
                ret.extend(do_query(value, q[1:]))
            else:
                ret.extend(do_query(value, q))
    return ret


def query(data, query_string):
    q = parse(query_string)

    return do_query(data, q)


def request(query, params):
    query = urlencode({'q': query})[2:]

    fp = {'query': query}
    if paging and search_url.find('{pageno}') >= 0:
        fp['pageno'] = (params['pageno'] - 1) * page_size + first_page_num

    params['cookies'].update(cookies)
    params['headers'].update(headers)

    params['url'] = search_url.format(**fp)
    params['query'] = query

    return params


def identity(arg):
    return arg


def response(resp):
    results = []
    json = loads(resp.text)

    title_filter = html_to_text if title_html_to_text else identity
    content_filter = html_to_text if content_html_to_text else identity

    if results_query:
        rs = query(json, results_query)
        if not len(rs):
            return results
        for result in rs[0]:
            try:
                url = query(result, url_query)[0]
                title = query(result, title_query)[0]
            except:
                continue
            try:
                content = query(result, content_query)[0]
            except:
                content = ""
            results.append(
                {
                    'url': to_string(url),
                    'title': title_filter(to_string(title)),
                    'content': content_filter(to_string(content)),
                }
            )
    else:
        for url, title, content in zip(query(json, url_query), query(json, title_query), query(json, content_query)):
            results.append(
                {
                    'url': to_string(url),
                    'title': title_filter(to_string(title)),
                    'content': content_filter(to_string(content)),
                }
            )

    if not suggestion_query:
        return results
    for suggestion in query(json, suggestion_query):
        results.append({'suggestion': suggestion})
    return results
