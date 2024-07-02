# SPDX-License-Identifier: AGPL-3.0-or-later
"""YaCy_ is a free distributed search engine, built on the principles of
peer-to-peer (P2P) networks.

API: Dev:APIyacysearch_

Releases:

- https://github.com/yacy/yacy_search_server/tags
- https://download.yacy.net/

.. _Yacy: https://yacy.net/
.. _Dev:APIyacysearch: https://wiki.yacy.net/index.php/Dev:APIyacysearch

Configuration
=============

The engine has the following (additional) settings:

- :py:obj:`http_digest_auth_user`
- :py:obj:`http_digest_auth_pass`
- :py:obj:`search_mode`
- :py:obj:`search_type`

The :py:obj:`base_url` has to be set in the engine named `yacy` and is used by
all yacy engines.

.. code:: yaml

  - name: yacy
    engine: yacy
    categories: general
    search_type: text
    shortcut: ya
    base_url:
      - https://yacy.searchlab.eu
      - https://search.lomig.me
      - https://yacy.ecosys.eu
      - https://search.webproject.link

  - name: yacy images
    engine: yacy
    categories: images
    search_type: image
    shortcut: yai
    disabled: true


Implementations
===============
"""
# pylint: disable=fixme

from __future__ import annotations

import random
from json import loads
from urllib.parse import urlencode
from dateutil import parser

from httpx import DigestAuth

from searx.utils import html_to_text

# about
about = {
    "website": 'https://yacy.net/',
    "wikidata_id": 'Q1759675',
    "official_api_documentation": 'https://wiki.yacy.net/index.php/Dev:API',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ['general']
paging = True
number_of_results = 10
http_digest_auth_user = ""
"""HTTP digest user for the local YACY instance"""
http_digest_auth_pass = ""
"""HTTP digest password for the local YACY instance"""

search_mode = 'global'
"""Yacy search mode ``global`` or ``local``.  By default, Yacy operates in ``global``
mode.

``global``
  Peer-to-Peer search

``local``
  Privacy or Stealth mode, restricts the search to local yacy instance.
"""
search_type = 'text'
"""One of ``text``, ``image`` / The search-types ``app``, ``audio`` and
``video`` are not yet implemented (Pull-Requests are welcome).
"""

base_url: list | str = 'https://yacy.searchlab.eu'
"""The value is an URL or a list of URLs.  In the latter case instance will be
selected randomly.
"""


def init(_):
    valid_types = [
        'text',
        'image',
        # 'app', 'audio', 'video',
    ]
    if search_type not in valid_types:
        raise ValueError('search_type "%s" is  not one of %s' % (search_type, valid_types))


def _base_url() -> str:
    from searx.engines import engines  # pylint: disable=import-outside-toplevel

    url = engines['yacy'].base_url  # type: ignore
    if isinstance(url, list):
        url = random.choice(url)
    if url.endswith("/"):
        url = url[:-1]
    return url


def request(query, params):

    offset = (params['pageno'] - 1) * number_of_results
    args = {
        'query': query,
        'startRecord': offset,
        'maximumRecords': number_of_results,
        'contentdom': search_type,
        'resource': search_mode,
    }

    # add language tag if specified
    if params['language'] != 'all':
        args['lr'] = 'lang_' + params['language'].split('-')[0]

    params["url"] = f"{_base_url()}/yacysearch.json?{urlencode(args)}"

    if http_digest_auth_user and http_digest_auth_pass:
        params['auth'] = DigestAuth(http_digest_auth_user, http_digest_auth_pass)

    return params


def response(resp):
    results = []

    raw_search_results = loads(resp.text)

    # return empty array if there are no results
    if not raw_search_results:
        return []

    search_results = raw_search_results.get('channels', [])

    if len(search_results) == 0:
        return []

    for result in search_results[0].get('items', []):
        # parse image results
        if search_type == 'image':
            result_url = ''
            if 'url' in result:
                result_url = result['url']
            elif 'link' in result:
                result_url = result['link']
            else:
                continue

            # append result
            results.append(
                {
                    'url': result_url,
                    'title': result['title'],
                    'content': '',
                    'img_src': result['image'],
                    'template': 'images.html',
                }
            )

        # parse general results
        else:
            publishedDate = None
            if 'pubDate' in result:
                publishedDate = parser.parse(result['pubDate'])

            # append result
            results.append(
                {
                    'url': result['link'] or '',
                    'title': result['title'],
                    'content': html_to_text(result['description']),
                    'publishedDate': publishedDate,
                }
            )

        # TODO parse video, audio and file results

    return results
