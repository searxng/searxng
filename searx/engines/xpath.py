# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""The XPath engine is a *generic* engine with which it is possible to configure
engines in the settings.

.. _XPath selector: https://quickref.me/xpath.html#xpath-selectors

Configuration
=============

Request:

- :py:obj:`search_url`
- :py:obj:`lang_all`
- :py:obj:`soft_max_redirects`
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

- :py:obj:`no_result_for_http_status`

`XPath selector`_:

- :py:obj:`results_xpath`
- :py:obj:`url_xpath`
- :py:obj:`title_xpath`
- :py:obj:`content_xpath`
- :py:obj:`thumbnail_xpath`
- :py:obj:`suggestion_xpath`


Example
=======

Here is a simple example of a XPath engine configured in the :ref:`settings
engine` section, further read :ref:`engines-dev`.

.. code:: yaml

  - name : bitbucket
    engine : xpath
    paging : True
    search_url : https://bitbucket.org/repo/all/{pageno}?name={query}
    url_xpath : //article[@class="repo-summary"]//a[@class="repo-link"]/@href
    title_xpath : //article[@class="repo-summary"]//a[@class="repo-link"]
    content_xpath : //article[@class="repo-summary"]/p

Implementations
===============

"""

from urllib.parse import urlencode

from lxml import html
from searx.utils import extract_text, extract_url, eval_xpath, eval_xpath_list
from searx.network import raise_for_httperror

search_url = None
"""
Search URL of the engine.  Example::

    https://example.org/?search={query}&page={pageno}{time_range}{safe_search}

Replacements are:

``{query}``:
  Search terms from user.

``{pageno}``:
  Page number if engine supports pagging :py:obj:`paging`

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

results_xpath = ''
'''`XPath selector`_ for the list of result items'''

url_xpath = None
'''`XPath selector`_ of result's ``url``.'''

content_xpath = None
'''`XPath selector`_ of result's ``content``.'''

title_xpath = None
'''`XPath selector`_ of result's ``title``.'''

thumbnail_xpath = False
'''`XPath selector`_ of result's ``img_src``.'''

suggestion_xpath = ''
'''`XPath selector`_ of result's ``suggestion``.'''

cached_xpath = ''
cached_url = ''

cookies = {}
'''Some engines might offer different result based on cookies.
Possible use-case: To set safesearch cookie.'''

headers = {}
'''Some engines might offer different result based headers.  Possible use-case:
To set header to moderate.'''

paging = False
'''Engine supports paging [True or False].'''

page_size = 1
'''Number of results on each page.  Only needed if the site requires not a page
number, but an offset.'''

first_page_num = 1
'''Number of the first page (usually 0 or 1).'''

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


def request(query, params):
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

    fargs = {
        'query': urlencode({'q': query})[2:],
        'lang': lang,
        'pageno': (params['pageno'] - 1) * page_size + first_page_num,
        'time_range': time_range,
        'safe_search': safe_search,
    }

    params['cookies'].update(cookies)
    params['headers'].update(headers)

    params['url'] = search_url.format(**fargs)
    params['soft_max_redirects'] = soft_max_redirects

    params['raise_for_httperror'] = False

    return params


def response(resp):  # pylint: disable=too-many-branches
    '''Scrap *results* from the response (see :ref:`engine results`).'''
    if no_result_for_http_status and resp.status_code in no_result_for_http_status:
        return []

    raise_for_httperror(resp)

    results = []
    dom = html.fromstring(resp.text)
    is_onion = 'onions' in categories

    if results_xpath:
        for result in eval_xpath_list(dom, results_xpath):

            url = extract_url(eval_xpath_list(result, url_xpath, min_len=1), search_url)
            title = extract_text(eval_xpath_list(result, title_xpath, min_len=1))
            content = extract_text(eval_xpath_list(result, content_xpath))
            tmp_result = {'url': url, 'title': title, 'content': content}

            # add thumbnail if available
            if thumbnail_xpath:
                thumbnail_xpath_result = eval_xpath_list(result, thumbnail_xpath)
                if len(thumbnail_xpath_result) > 0:
                    tmp_result['img_src'] = extract_url(thumbnail_xpath_result, search_url)

            # add alternative cached url if available
            if cached_xpath:
                tmp_result['cached_url'] = cached_url + extract_text(eval_xpath_list(result, cached_xpath, min_len=1))

            if is_onion:
                tmp_result['is_onion'] = True

            results.append(tmp_result)

    else:
        if cached_xpath:
            for url, title, content, cached in zip(
                (extract_url(x, search_url) for x in eval_xpath_list(dom, url_xpath)),
                map(extract_text, eval_xpath_list(dom, title_xpath)),
                map(extract_text, eval_xpath_list(dom, content_xpath)),
                map(extract_text, eval_xpath_list(dom, cached_xpath)),
            ):
                results.append(
                    {
                        'url': url,
                        'title': title,
                        'content': content,
                        'cached_url': cached_url + cached,
                        'is_onion': is_onion,
                    }
                )
        else:
            for url, title, content in zip(
                (extract_url(x, search_url) for x in eval_xpath_list(dom, url_xpath)),
                map(extract_text, eval_xpath_list(dom, title_xpath)),
                map(extract_text, eval_xpath_list(dom, content_xpath)),
            ):
                results.append({'url': url, 'title': title, 'content': content, 'is_onion': is_onion})

    if suggestion_xpath:
        for suggestion in eval_xpath(dom, suggestion_xpath):
            results.append({'suggestion': extract_text(suggestion)})

    logger.debug("found %s results", len(results))
    return results
