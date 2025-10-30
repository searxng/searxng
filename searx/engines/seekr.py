# SPDX-License-Identifier: AGPL-3.0-or-later
"""seekr.com Seeker Score

Seekr is a privately held search and content evaluation engine that prioritizes
credibility over popularity.

Configuration
=============

The engine has the following additional settings:

- :py:obj:`seekr_category`
- :py:obj:`api_key`

This implementation is used by seekr engines in the :ref:`settings.yml
<settings engines>`:

.. code:: yaml

  - name: seekr news
    seekr_category: news
    ...
  - name: seekr images
    seekr_category: images
    ...
  - name: seekr videos
    seekr_category: videos
    ...

Known Quirks
============

The implementation to support :py:obj:`paging <searx.enginelib.Engine.paging>`
is based on the *nextpage* method of Seekr's REST API.  This feature is *next
page driven* and plays well with the :ref:`infinite_scroll <settings plugins>`
plugin in SearXNG but it does not really fit into SearXNG's UI to select a page
by number.

Implementations
===============

"""

from datetime import datetime
from json import loads
from urllib.parse import urlencode
from flask_babel import gettext

about = {
    "website": 'https://seekr.com/',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": True,
    "results": 'JSON',
    "language": 'en',
}

base_url = "https://api.seekr.com"
paging = True

api_key = "srh1-22fb-sekr"
"""API key / reversed engineered / is still the same one since 2022."""

seekr_category: str = 'unset'
"""Search category, any of ``news``, ``videos`` or ``images``."""


def init(engine_settings):

    # global paging
    if engine_settings['seekr_category'] not in ['news', 'videos', 'images']:
        raise ValueError(f"Unsupported seekr category: {engine_settings['seekr_category']}")


def request(query, params):

    if not query:
        return None

    args = {
        'query': query,
        'apiKey': api_key,
    }

    api_url = base_url + '/engine'
    if seekr_category == 'news':
        api_url += '/v2/newssearch'

    elif seekr_category == 'images':
        api_url += '/imagetab'

    elif seekr_category == 'videos':
        api_url += '/videotab'

    params['url'] = f"{api_url}?{urlencode(args)}"
    if params['pageno'] > 1:
        nextpage = params['engine_data'].get('nextpage')
        if nextpage:
            params['url'] = nextpage

    return params


def _images_response(json):

    search_results = json.get('expertResponses')
    if search_results:
        search_results = search_results[0].get('advice')
    else:  # response from a 'nextResultSet'
        search_results = json.get('advice')

    results = []
    if not search_results:
        return results

    for result in search_results['results']:
        summary = loads(result['summary'])
        results.append(
            {
                'template': 'images.html',
                'url': summary['refererurl'],
                'title': result['title'],
                'img_src': result['url'],
                'resolution': f"{summary['width']}x{summary['height']}",
                'thumbnail_src': 'https://media.seekr.com/engine/rp/' + summary['tg'] + '/?src= ' + result['thumbnail'],
            }
        )

    if search_results.get('nextResultSet'):
        results.append(
            {
                "engine_data": search_results.get('nextResultSet'),
                "key": "nextpage",
            }
        )
    return results


def _videos_response(json):

    search_results = json.get('expertResponses')
    if search_results:
        search_results = search_results[0].get('advice')
    else:  # response from a 'nextResultSet'
        search_results = json.get('advice')

    results = []
    if not search_results:
        return results

    for result in search_results['results']:
        summary = loads(result['summary'])
        results.append(
            {
                'template': 'videos.html',
                'url': result['url'],
                'title': result['title'],
                'thumbnail': 'https://media.seekr.com/engine/rp/' + summary['tg'] + '/?src= ' + result['thumbnail'],
            }
        )

    if search_results.get('nextResultSet'):
        results.append(
            {
                "engine_data": search_results.get('nextResultSet'),
                "key": "nextpage",
            }
        )
    return results


def _news_response(json):

    search_results = json.get('expertResponses')
    if search_results:
        search_results = search_results[0]['advice']['categorySearchResult']['searchResult']
    else:  # response from a 'nextResultSet'
        search_results = json.get('advice')

    results = []
    if not search_results:
        return results

    for result in search_results['results']:

        results.append(
            {
                'url': result['url'],
                'title': result['title'],
                'content': result['summary'] or result["topCategory"] or result["displayUrl"] or '',
                'thumbnail': result.get('thumbnail', ''),
                'publishedDate': datetime.strptime(result['pubDate'][:19], '%Y-%m-%d %H:%M:%S'),
                'metadata': gettext("Language") + ': ' + result.get('language', ''),
            }
        )

    if search_results.get('nextResultSet'):
        results.append(
            {
                "engine_data": search_results.get('nextResultSet'),
                "key": "nextpage",
            }
        )
    return results


def response(resp):
    json = resp.json()

    if seekr_category == "videos":
        return _videos_response(json)
    if seekr_category == "images":
        return _images_response(json)
    if seekr_category == "news":
        return _news_response(json)

    raise ValueError(f"Unsupported seekr category: {seekr_category}")
