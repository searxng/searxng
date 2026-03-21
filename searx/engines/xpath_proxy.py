# SPDX-License-Identifier: AGPL-3.0-or-later
"""The XPath Proxy engine is a *generic* engine that extends :ref:`xpath_engine`
by fetching pages through a configurable external rendering service instead of
making direct HTTP requests.

This is useful for search providers that require JavaScript rendering to return
meaningful results.  The rendering service is a black box — it receives a URL,
renders it (e.g. using a headless browser), and returns either:

- **Structured JSON**: pre-extracted results, suggestions, and CAPTCHA status.
- **Raw HTML**: the engine parses it locally using XPath selectors (same as
  :ref:`xpath_engine`).

.. _XPath selector: https://quickref.me/xpath.html#xpath-selectors

Configuration
=============

Proxy:

- :py:obj:`proxy_url`
- :py:obj:`proxy_endpoint`
- :py:obj:`proxy_profile`
- :py:obj:`render_timeout`

Request (inherited from :ref:`xpath_engine`):

- :py:obj:`search_url`
- :py:obj:`lang_all`
- :py:obj:`cookies`
- :py:obj:`headers`

Paging (inherited from :ref:`xpath_engine`):

- :py:obj:`paging`
- :py:obj:`page_size`
- :py:obj:`first_page_num`

Time Range (inherited from :ref:`xpath_engine`):

- :py:obj:`time_range_support`
- :py:obj:`time_range_url`
- :py:obj:`time_range_map`

Safe-Search (inherited from :ref:`xpath_engine`):

- :py:obj:`safe_search_support`
- :py:obj:`safe_search_map`

`XPath selector`_ (used when rendering service returns raw HTML):

- :py:obj:`results_xpath`
- :py:obj:`url_xpath`
- :py:obj:`title_xpath`
- :py:obj:`content_xpath`
- :py:obj:`thumbnail_xpath`
- :py:obj:`suggestion_xpath`


Example
=======

Structured mode (rendering service returns pre-extracted results):

.. code:: yaml

  - name: google (browser)
    engine: xpath_proxy
    proxy_url: http://rendering-service:8080
    proxy_profile: google_web
    search_url: https://www.google.com/search?q={query}&hl={lang}&start={pageno}
    paging: true
    page_size: 10
    first_page_num: 0
    categories: [general, web]
    timeout: 45.0

Raw HTML mode (rendering service returns HTML, engine parses with XPath):

.. code:: yaml

  - name: example (browser)
    engine: xpath_proxy
    proxy_url: http://rendering-service:8080
    search_url: https://example.com/search?q={query}&page={pageno}
    results_xpath: //div[@class="result"]
    url_xpath: .//a/@href
    title_xpath: .//h3
    content_xpath: .//p
    paging: true
    categories: [general]

Implementations
===============

"""

from urllib.parse import urlencode

from lxml import html
from searx.exceptions import SearxEngineCaptchaException, SearxEngineAPIException
from searx.utils import extract_text, extract_url, eval_xpath, eval_xpath_list
from searx.result_types import EngineResults

# Proxy configuration
# -------------------

proxy_url = None
"""Base URL of the external rendering service.  **Required.**

.. code:: yaml

    proxy_url: http://rendering-service:8080
"""

proxy_endpoint = '/extract'
"""Endpoint path on the rendering service.

.. code:: yaml

    proxy_endpoint: /extract
"""

proxy_profile = ''
"""Server-side extraction profile name.  When set, the rendering service uses
this profile to extract structured results.  When not set, the service returns
raw HTML and the engine parses it locally using XPath selectors.

.. code:: yaml

    proxy_profile: google_web
"""

render_timeout = 0
"""Optional timeout override for the rendering service (in milliseconds).  When
set to 0 (the default), the rendering service uses its own default timeout.

.. code:: yaml

    render_timeout: 30000
"""

# Request configuration (same as xpath engine)
# ---------------------------------------------

search_url = None
"""Search URL of the engine, same as :ref:`xpath_engine`.  Example::

    https://example.org/?search={query}&page={pageno}{time_range}{safe_search}
"""

lang_all = 'en'
'''Replacement ``{lang}`` in :py:obj:`search_url` if language ``all`` is
selected.
'''

cookies = {}
'''Cookies to forward to the rendering service in the request payload.'''

headers = {}
'''Headers to forward to the rendering service in the request payload.'''

# Paging configuration
# --------------------

paging = False
'''Engine supports paging [True or False].'''

page_size = 1
'''Number of results on each page.  Only needed if the site requires not a page
number, but an offset.'''

first_page_num = 1
'''Number of the first page (usually 0 or 1).'''

# Time Range configuration
# ------------------------

time_range_support = False
'''Engine supports search time range.'''

time_range_url = '&hours={time_range_val}'
'''Time range URL parameter in the :py:obj:`search_url`.'''

time_range_map = {
    'day': 24,
    'week': 24 * 7,
    'month': 24 * 30,
    'year': 24 * 365,
}
'''Maps time range value from user to ``{time_range_val}`` in
:py:obj:`time_range_url`.'''

# Safe Search configuration
# -------------------------

safe_search_support = False
'''Engine supports safe-search.'''

safe_search_map = {0: '&filter=none', 1: '&filter=moderate', 2: '&filter=strict'}
'''Maps safe-search value to ``{safe_search}`` in :py:obj:`search_url`.'''

# XPath selectors (used in raw HTML mode only)
# ---------------------------------------------

results_xpath = ''
'''`XPath selector`_ for the list of result items.'''

url_xpath = ''
'''`XPath selector`_ of result's ``url``.'''

content_xpath = ''
'''`XPath selector`_ of result's ``content``.'''

title_xpath = ''
'''`XPath selector`_ of result's ``title``.'''

thumbnail_xpath = ''
'''`XPath selector`_ of result's ``thumbnail``.'''

suggestion_xpath = ''
'''`XPath selector`_ of result's ``suggestion``.'''

cached_xpath = ''
cached_url = ''


def request(query, params):
    '''Build request parameters for the rendering service.

    Constructs the target search URL (same as :ref:`xpath_engine`) and wraps it
    in a POST request to the rendering service.
    '''
    lang = lang_all
    if params['language'] != 'all':
        lang = params['language'][:2]

    time_range = ''
    if params.get('time_range'):
        time_range_val = time_range_map.get(params.get('time_range'))
        time_range = time_range_url.format(time_range_val=time_range_val)

    safe_search = ''
    safe_search_val = params.get('safesearch')
    if safe_search_val is not None:
        safe_search = safe_search_map[safe_search_val]

    fargs = {
        'query': urlencode({'q': query})[2:],
        'lang': lang,
        'pageno': (params['pageno'] - 1) * page_size + first_page_num,
        'time_range': time_range,
        'safe_search': safe_search,
    }

    target_url = search_url.format(**fargs)

    # Build the rendering service request payload
    payload = {'url': target_url}

    if proxy_profile:
        payload['profile'] = proxy_profile
    if render_timeout:
        payload['timeout'] = render_timeout

    # POST to the rendering service
    params['url'] = f"{proxy_url}{proxy_endpoint}"
    params['method'] = 'POST'
    params['json'] = payload

    # Don't forward SearXNG's own headers/cookies to the rendering service;
    # the service manages its own browser headers.  Engine-level cookies and
    # headers are included in the payload for the rendering service to use
    # if needed.
    if cookies:
        payload['cookies'] = cookies
    if headers:
        payload['headers'] = headers

    params['cookies'] = {}
    params['headers'] = {'Content-Type': 'application/json'}

    return params


def response(resp) -> EngineResults:
    '''Parse results from the rendering service response.

    Supports two response formats:

    **Structured** (rendering service extracted results server-side)::

        {"results": [{"url": ..., "title": ..., "content": ...}, ...],
         "suggestions": ["...", ...],
         "captcha": false,
         "error": null}

    **Raw HTML** (rendering service returned rendered page source)::

        {"html": "<html>...</html>",
         "url": "https://...",
         "captcha": false,
         "error": null}
    '''
    results = EngineResults()

    try:
        data = resp.json()
    except Exception as exc:
        raise SearxEngineAPIException("Invalid JSON response from rendering service") from exc

    # CAPTCHA detected by the rendering service
    if data.get('captcha'):
        raise SearxEngineCaptchaException()

    # Rendering service reported an error
    error = data.get('error')
    if error:
        raise SearxEngineAPIException(error)

    # Structured mode: rendering service returned pre-extracted results
    if 'results' in data:
        for item in data['results']:
            url = item.get('url', '')
            title = item.get('title', '')
            content = item.get('content', '')
            if not url or not title:
                continue
            tmp_result = {'url': url, 'title': title, 'content': content}

            thumbnail = item.get('thumbnail')
            if thumbnail:
                tmp_result['thumbnail'] = thumbnail

            results.append(tmp_result)

        for suggestion in data.get('suggestions', []):
            results.append({'suggestion': suggestion})

    # Raw HTML mode: rendering service returned rendered page source
    elif 'html' in data:
        page_html = data['html']
        if page_html:
            _parse_html(page_html, results)

    logger.debug("found %s results", len(results))
    return results


def _parse_html(page_html, results):
    '''Parse raw HTML using XPath selectors (same logic as :ref:`xpath_engine`).'''

    dom = html.fromstring(page_html)
    is_onion = 'onions' in categories  # noqa: F821

    if results_xpath:
        for result in eval_xpath_list(dom, results_xpath):

            url = extract_url(eval_xpath_list(result, url_xpath, min_len=1), search_url)
            title = extract_text(eval_xpath_list(result, title_xpath, min_len=1))
            content = extract_text(eval_xpath_list(result, content_xpath))
            tmp_result = {'url': url, 'title': title, 'content': content}

            if thumbnail_xpath:
                thumbnail_xpath_result = eval_xpath_list(result, thumbnail_xpath)
                if len(thumbnail_xpath_result) > 0:
                    tmp_result['thumbnail'] = extract_url(thumbnail_xpath_result, search_url)

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
