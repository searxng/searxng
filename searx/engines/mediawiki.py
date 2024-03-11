# SPDX-License-Identifier: AGPL-3.0-or-later
"""The MediaWiki engine is a *generic* engine to **query** Wikimedia wikis by
the `MediaWiki Action API`_.  For a `query action`_ all Wikimedia wikis have
endpoints that follow this pattern::

    https://{base_url}/w/api.php?action=query&list=search&format=json

.. note::

   In its actual state, this engine is implemented to parse JSON result
   (`format=json`_) from a search query (`list=search`_).  If you need other
   ``action`` and ``list`` types ask SearXNG developers to extend the
   implementation according to your needs.

.. _MediaWiki Action API: https://www.mediawiki.org/wiki/API:Main_page
.. _query action: https://www.mediawiki.org/w/api.php?action=help&modules=query
.. _`list=search`: https://www.mediawiki.org/w/api.php?action=help&modules=query%2Bsearch
.. _`format=json`: https://www.mediawiki.org/w/api.php?action=help&modules=json

Configuration
=============

Request:

- :py:obj:`base_url`
- :py:obj:`search_type`
- :py:obj:`srenablerewrites`
- :py:obj:`srsort`
- :py:obj:`srprop`

Implementations
===============

"""
from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import datetime
from urllib.parse import urlencode, quote

from searx.utils import html_to_text
from searx.enginelib.traits import EngineTraits

if TYPE_CHECKING:
    import logging

    logger: logging.Logger

traits: EngineTraits

# about
about = {
    "website": None,
    "wikidata_id": None,
    "official_api_documentation": 'https://www.mediawiki.org/w/api.php?action=help&modules=query',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ['general']
paging = True
number_of_results = 5

search_type: str = 'nearmatch'
"""Which type of search to perform.  One of the following values: ``nearmatch``,
``text`` or ``title``.

See ``srwhat`` argument in `list=search`_ documentation.
"""

srenablerewrites: bool = True
"""Enable internal query rewriting (Type: boolean).  Some search backends can
rewrite the query into another which is thought to provide better results, for
instance by correcting spelling errors.

See ``srenablerewrites`` argument in `list=search`_ documentation.
"""

srsort: str = 'relevance'
"""Set the sort order of returned results.  One of the following values:
``create_timestamp_asc``, ``create_timestamp_desc``, ``incoming_links_asc``,
``incoming_links_desc``, ``just_match``, ``last_edit_asc``, ``last_edit_desc``,
``none``, ``random``, ``relevance``, ``user_random``.

See ``srenablerewrites`` argument in `list=search`_ documentation.
"""

srprop: str = 'sectiontitle|snippet|timestamp|categorysnippet'
"""Which properties to return.

See ``srprop`` argument in `list=search`_ documentation.
"""

base_url: str = 'https://{language}.wikipedia.org/'
"""Base URL of the Wikimedia wiki.

``{language}``:
  ISO 639-1 language code (en, de, fr ..) of the search language.
"""

timestamp_format = '%Y-%m-%dT%H:%M:%SZ'
"""The longhand version of MediaWiki time strings."""


def request(query, params):

    # write search-language back to params, required in response

    if params['language'] == 'all':
        params['language'] = 'en'
    else:
        params['language'] = params['language'].split('-')[0]

    if base_url.endswith('/'):
        api_url = base_url + 'w/api.php?'
    else:
        api_url = base_url + '/w/api.php?'
    api_url = api_url.format(language=params['language'])

    offset = (params['pageno'] - 1) * number_of_results

    args = {
        'action': 'query',
        'list': 'search',
        'format': 'json',
        'srsearch': query,
        'sroffset': offset,
        'srlimit': number_of_results,
        'srwhat': search_type,
        'srprop': srprop,
        'srsort': srsort,
    }
    if srenablerewrites:
        args['srenablerewrites'] = '1'

    params['url'] = api_url + urlencode(args)
    return params


# get response from search-request
def response(resp):

    results = []
    search_results = resp.json()

    # return empty array if there are no results
    if not search_results.get('query', {}).get('search'):
        return []

    for result in search_results['query']['search']:

        if result.get('snippet', '').startswith('#REDIRECT'):
            continue

        title = result['title']
        sectiontitle = result.get('sectiontitle')
        content = html_to_text(result.get('snippet', ''))
        metadata = html_to_text(result.get('categorysnippet', ''))
        timestamp = result.get('timestamp')

        url = (
            base_url.format(language=resp.search_params['language']) + 'wiki/' + quote(title.replace(' ', '_').encode())
        )
        if sectiontitle:
            # in case of sectiontitle create a link to the section in the wiki page
            url += '#' + quote(sectiontitle.replace(' ', '_').encode())
            title += ' / ' + sectiontitle

        item = {'url': url, 'title': title, 'content': content, 'metadata': metadata}

        if timestamp:
            item['publishedDate'] = datetime.strptime(timestamp, timestamp_format)

        results.append(item)

    # return results
    return results
