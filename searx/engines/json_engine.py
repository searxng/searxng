# SPDX-License-Identifier: AGPL-3.0-or-later
"""The JSON engine is a *generic* engine with which it is possible to configure
engines in the settings.

Configuration
=============

Request:

- :py:obj:`search_url`
- :py:obj:`method`
- :py:obj:`request_body`
- :py:obj:`cookies`
- :py:obj:`headers`

Paging:

- :py:obj:`paging`
- :py:obj:`page_size`
- :py:obj:`first_page_num`

Response:

- :py:obj:`title_html_to_text`
- :py:obj:`content_html_to_text`

JSON query:

- :py:obj:`results_query`
- :py:obj:`url_query`
- :py:obj:`url_prefix`
- :py:obj:`title_query`
- :py:obj:`content_query`
- :py:obj:`suggestion_query`


Example
=======

Here is a simple example of a JSON engine configure in the :ref:`settings
engine` section, further read :ref:`engines-dev`.

.. code:: yaml

  - name : mdn
    engine : json_engine
    paging : True
    search_url : https://developer.mozilla.org/api/v1/search?q={query}&page={pageno}
    results_query : documents
    url_query : mdn_url
    url_prefix : https://developer.mozilla.org
    title_query : title
    content_query : summary

Implementations
===============

"""

from collections.abc import Iterable
from json import loads
from urllib.parse import urlencode
from searx.utils import to_string, html_to_text

search_url = None
"""
Search URL of the engine.  Example::

    https://example.org/?search={query}&page={pageno}

Replacements are:

``{query}``:
  Search terms from user.

``{pageno}``:
  Page number if engine supports paging :py:obj:`paging`

"""

method = 'GET'
'''Some engines might require to do POST requests for search.'''

request_body = ''
'''The body of the request.  This can only be used if different :py:obj:`method`
is set, e.g. ``POST``. For formatting see the documentation of :py:obj:`search_url`.

Note: Curly brackets which aren't encapsulating a replacement placeholder
must be escaped by doubling each ``{`` and ``}``.

.. code:: yaml

    request_body: >-
      {{
        "search": "{query}",
        "page": {pageno},
        "extra": {{
          "time_range": {time_range},
          "rating": "{safe_search}"
        }}
      }}
'''

cookies = {}
'''Some engines might offer different result based on cookies.
Possible use-case: To set safesearch cookie.'''

headers = {}
'''Some engines might offer different result based on cookies or headers.
Possible use-case: To set safesearch cookie or header to moderate.'''

paging = False
'''Engine supports paging [True or False].'''

page_size = 1
'''Number of results on each page.  Only needed if the site requires not a page
number, but an offset.'''

first_page_num = 1
'''Number of the first page (usually 0 or 1).'''

results_query = ''
'''JSON query for the list of result items.

The query string is a slash `/` separated path of JSON key names.
Array entries can be specified using the index or can be omitted entirely,
in which case each entry is considered -
most implementations will default to the first entry in this case.
'''

url_query = None
'''JSON query of result's ``url``. For the query string documentation see :py:obj:`results_query`'''

url_prefix = ""
'''String to prepend to the result's ``url``.'''

title_query = None
'''JSON query of result's ``title``. For the query string documentation see :py:obj:`results_query`'''

content_query = None
'''JSON query of result's ``content``. For the query string documentation see :py:obj:`results_query`'''

suggestion_query = ''
'''JSON query of result's ``suggestion``. For the query string documentation see :py:obj:`results_query`'''

title_html_to_text = False
'''Extract text from a HTML title string'''

content_html_to_text = False
'''Extract text from a HTML content string'''


def iterate(iterable):
    if isinstance(iterable, dict):
        items = iterable.items()

    else:
        items = enumerate(iterable)
    for index, value in items:
        yield str(index), value


def is_iterable(obj):
    if isinstance(obj, str):
        return False
    return isinstance(obj, Iterable)


def parse(query):  # pylint: disable=redefined-outer-name
    q = []  # pylint: disable=invalid-name
    for part in query.split('/'):
        if part == '':
            continue
        q.append(part)
    return q


def do_query(data, q):  # pylint: disable=invalid-name
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


def request(query, params):  # pylint: disable=redefined-outer-name
    '''Build request parameters (see :ref:`engine request`).'''
    fp = {'query': urlencode({'q': query})[2:]}  # pylint: disable=invalid-name

    if paging and search_url.find('{pageno}') >= 0:
        fp['pageno'] = (params['pageno'] - 1) * page_size + first_page_num

    params['cookies'].update(cookies)
    params['headers'].update(headers)

    params['url'] = search_url.format(**fp)
    params['method'] = method

    if request_body:
        # don't url-encode the query if it's in the request body
        fp['query'] = query
        params['data'] = request_body.format(**fp)

    return params


def identity(arg):
    return arg


def response(resp):
    '''Scrap *results* from the response (see :ref:`engine results`).'''
    results = []

    if not resp.text:
        return results

    json = loads(resp.text)

    title_filter = html_to_text if title_html_to_text else identity
    content_filter = html_to_text if content_html_to_text else identity

    if results_query:
        rs = query(json, results_query)  # pylint: disable=invalid-name
        if not rs:
            return results
        for result in rs[0]:
            try:
                url = query(result, url_query)[0]
                title = query(result, title_query)[0]
            except:  # pylint: disable=bare-except
                continue
            try:
                content = query(result, content_query)[0]
            except:  # pylint: disable=bare-except
                content = ""
            results.append(
                {
                    'url': url_prefix + to_string(url),
                    'title': title_filter(to_string(title)),
                    'content': content_filter(to_string(content)),
                }
            )
    else:
        for result in json:
            url = query(result, url_query)[0]
            title = query(result, title_query)[0]
            content = query(result, content_query)[0]

            results.append(
                {
                    'url': url_prefix + to_string(url),
                    'title': title_filter(to_string(title)),
                    'content': content_filter(to_string(content)),
                }
            )

    if not suggestion_query:
        return results
    for suggestion in query(json, suggestion_query):
        results.append({'suggestion': suggestion})
    return results
