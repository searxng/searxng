# SPDX-License-Identifier: AGPL-3.0-or-later
"""The JSON engine is a *generic* engine with which it is possible to configure
engines in the settings.

Configuration
=============

Request:

- :py:obj:`search_url`
- :py:obj:`lang_all`
- :py:obj:`soft_max_redirects`
- :py:obj:`method`
- :py:obj:`request_body`
- :py:obj:`cookies`
- :py:obj:`headers`

Paging:

- :py:obj:`paging`
- :py:obj:`page_size`
- :py:obj:`first_page_num`

Time Range:

- :py:obj:`time_range_support`
- :py:obj:`time_range_url`
- :py:obj:`time_range_map`

Safe-Search:

- :py:obj:`safe_search_support`
- :py:obj:`safe_search_map`

Response:

- :py:obj:`title_html_to_text`
- :py:obj:`content_html_to_text`
- :py:obj:`no_result_for_http_status`

JSON query:

- :py:obj:`results_query`
- :py:obj:`url_query`
- :py:obj:`url_prefix`
- :py:obj:`title_query`
- :py:obj:`content_query`
- :py:obj:`thumbnail_query`
- :py:obj:`thumbnail_prefix`
- :py:obj:`suggestion_query`


Example
=======

Here is a simple example of a JSON engine configure in the :ref:`settings
engines` section, further read :ref:`engines-dev`.

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
from searx.network import raise_for_httperror

search_url = None
"""
Search URL of the engine.  Example::

    https://example.org/?search={query}&page={pageno}{time_range}{safe_search}

Replacements are:

``{query}``:
  Search terms from user.

``{pageno}``:
  Page number if engine supports paging :py:obj:`paging`

``{lang}``:
  ISO 639-1 language code (en, de, fr ..)

``{time_range}``:
  :py:obj:`URL parameter <time_range_url>` if engine :py:obj:`supports time
  range <time_range_support>`.  The value for the parameter is taken from
  :py:obj:`time_range_map`.

``{safe_search}``:
  Safe-search :py:obj:`URL parameter <safe_search_map>` if engine
  :py:obj:`supports safe-search <safe_search_support>`.  The ``{safe_search}``
  replacement is taken from the :py:obj:`safes_search_map`.  Filter results::

      0: none, 1: moderate, 2:strict

  If not supported, the URL parameter is an empty string.

"""

lang_all = 'en'
'''Replacement ``{lang}`` in :py:obj:`search_url` if language ``all`` is
selected.
'''

no_result_for_http_status = []
'''Return empty result for these HTTP status codes instead of throwing an error.

.. code:: yaml

    no_result_for_http_status: []
'''

soft_max_redirects = 0
'''Maximum redirects, soft limit. Record an error but don't stop the engine'''

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

thumbnail_query = False
'''JSON query of result's ``thumbnail``. For the query string documentation see :py:obj:`results_query`'''

thumbnail_prefix = ''
'''String to prepend to the result's ``thumbnail``.'''

suggestion_query = ''
'''JSON query of result's ``suggestion``. For the query string documentation see :py:obj:`results_query`'''

title_html_to_text = False
'''Extract text from a HTML title string'''

content_html_to_text = False
'''Extract text from a HTML content string'''

time_range_support = False
'''Engine supports search time range.'''

time_range_url = '&hours={time_range_val}'
'''Time range URL parameter in the in :py:obj:`search_url`.  If no time range is
requested by the user, the URL parameter is an empty string.  The
``{time_range_val}`` replacement is taken from the :py:obj:`time_range_map`.

.. code:: yaml

    time_range_url : '&days={time_range_val}'
'''

time_range_map = {
    'day': 24,
    'week': 24 * 7,
    'month': 24 * 30,
    'year': 24 * 365,
}
'''Maps time range value from user to ``{time_range_val}`` in
:py:obj:`time_range_url`.

.. code:: yaml

    time_range_map:
      day: 1
      week: 7
      month: 30
      year: 365
'''

safe_search_support = False
'''Engine supports safe-search.'''

safe_search_map = {0: '&filter=none', 1: '&filter=moderate', 2: '&filter=strict'}
'''Maps safe-search value to ``{safe_search}`` in :py:obj:`search_url`.

.. code:: yaml

    safesearch: true
    safes_search_map:
      0: '&filter=none'
      1: '&filter=moderate'
      2: '&filter=strict'

'''


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
    lang = lang_all
    if params['language'] != 'all':
        lang = params['language'][:2]

    time_range = ''
    if params.get('time_range'):
        time_range_val = time_range_map.get(params.get('time_range'))
        time_range = time_range_url.format(time_range_val=time_range_val)

    safe_search = ''
    if params['safesearch']:
        safe_search = safe_search_map[params['safesearch']]

    fp = {  # pylint: disable=invalid-name
        'query': urlencode({'q': query})[2:],
        'lang': lang,
        'pageno': (params['pageno'] - 1) * page_size + first_page_num,
        'time_range': time_range,
        'safe_search': safe_search,
    }

    params['cookies'].update(cookies)
    params['headers'].update(headers)

    params['url'] = search_url.format(**fp)
    params['method'] = method

    if request_body:
        # don't url-encode the query if it's in the request body
        fp['query'] = query
        params['data'] = request_body.format(**fp)

    params['soft_max_redirects'] = soft_max_redirects
    params['raise_for_httperror'] = False

    return params


def identity(arg):
    return arg


def extract_response_info(result):
    title_filter = html_to_text if title_html_to_text else identity
    content_filter = html_to_text if content_html_to_text else identity

    tmp_result = {}

    try:
        url = query(result, url_query)[0]
        tmp_result['url'] = url_prefix + to_string(url)

        title = query(result, title_query)[0]
        tmp_result['title'] = title_filter(to_string(title))
    except:  # pylint: disable=bare-except
        return None

    try:
        content = query(result, content_query)[0]
        tmp_result['content'] = content_filter(to_string(content))
    except:  # pylint: disable=bare-except
        tmp_result['content'] = ""

    try:
        if thumbnail_query:
            thumbnail_query_result = query(result, thumbnail_query)[0]
            tmp_result['thumbnail'] = thumbnail_prefix + to_string(thumbnail_query_result)
    except:  # pylint: disable=bare-except
        pass

    return tmp_result


def response(resp):
    '''Scrap *results* from the response (see :ref:`result types`).'''
    results = []

    if no_result_for_http_status and resp.status_code in no_result_for_http_status:
        return results

    raise_for_httperror(resp)

    if not resp.text:
        return results

    json = loads(resp.text)
    is_onion = 'onions' in categories

    if results_query:
        rs = query(json, results_query)  # pylint: disable=invalid-name
        if not rs:
            return results
        rs = rs[0]  # pylint: disable=invalid-name
    else:
        rs = json  # pylint: disable=invalid-name

    for result in rs:
        tmp_result = extract_response_info(result)
        if not tmp_result:
            continue

        if is_onion:
            tmp_result['is_onion'] = True

        results.append(tmp_result)

    if not suggestion_query:
        return results
    for suggestion in query(json, suggestion_query):
        results.append({'suggestion': suggestion})
    return results
