# SPDX-License-Identifier: AGPL-3.0-or-later
""".. sidebar:: info

  - `builtwith.com Discourse <https://trends.builtwith.com/websitelist/Discourse>`_

Discourse is an open source Internet forum system.  To search in a forum this
engine offers some additional settings:

- :py:obj:`base_url`
- :py:obj:`api_order`
- :py:obj:`search_endpoint`
- :py:obj:`show_avatar`
- :py:obj:`api_key`
- :py:obj:`api_username`

Example
=======

To search in your favorite Discourse forum, add a configuration like shown here
for the ``paddling.com`` forum:

.. code:: yaml

   - name: paddling
     engine: discourse
     shortcut: paddle
     base_url: 'https://forums.paddling.com/'
     api_order: views
     categories: ['social media', 'sports']
     show_avatar: true

If the forum is private, you need to add an API key and username for the search:

.. code:: yaml

   - name: paddling
     engine: discourse
     shortcut: paddle
     base_url: 'https://forums.paddling.com/'
     api_order: views
     categories: ['social media', 'sports']
     show_avatar: true
     api_key: '<KEY>'
     api_username: 'system'


Implementations
===============

"""

from urllib.parse import urlencode
from datetime import datetime, timedelta
import html

from dateutil import parser

from flask_babel import gettext

about = {
    "website": "https://discourse.org/",
    "wikidata_id": "Q15054354",
    "official_api_documentation": "https://docs.discourse.org/",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

base_url: str = None  # type: ignore
"""URL of the Discourse forum."""

search_endpoint = '/search.json'
"""URL path of the `search endpoint`_.

.. _search endpoint: https://docs.discourse.org/#tag/Search
"""

api_order = 'likes'
"""Order method, valid values are: ``latest``, ``likes``, ``views``, ``latest_topic``"""

show_avatar = False
"""Show avatar of the user who send the post."""

api_key = ''
"""API key of the Discourse forum."""

api_username = ''
"""API username of the Discourse forum."""

paging = True
time_range_support = True

AGO_TIMEDELTA = {
    'day': timedelta(days=1),
    'week': timedelta(days=7),
    'month': timedelta(days=31),
    'year': timedelta(days=365),
}


def request(query, params):

    if len(query) <= 2:
        return None

    q = [query, f'order:{api_order}']
    time_range = params.get('time_range')
    if time_range:
        after_date = datetime.now() - AGO_TIMEDELTA[time_range]
        q.append('after:' + after_date.strftime('%Y-%m-%d'))

    args = {
        'q': ' '.join(q),
        'page': params['pageno'],
    }

    params['url'] = f'{base_url}{search_endpoint}?{urlencode(args)}'
    params['headers'] = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
    }

    if api_key != '':
        params['headers']['Api-Key'] = api_key

    if api_username != '':
        params['headers']['Api-Username'] = api_username

    return params


def response(resp):

    results = []
    json_data = resp.json()

    if ('topics' or 'posts') not in json_data.keys():
        return []

    topics = {}

    for item in json_data['topics']:
        topics[item['id']] = item

    for post in json_data['posts']:
        result = topics.get(post['topic_id'], {})

        url = f"{base_url}/p/{post['id']}"
        status = gettext("closed") if result.get('closed', '') else gettext("open")
        comments = result.get('posts_count', 0)
        publishedDate = parser.parse(result['created_at'])

        metadata = []
        metadata.append('@' + post.get('username', ''))

        if int(comments) > 1:
            metadata.append(f'{gettext("comments")}: {comments}')

        if result.get('has_accepted_answer'):
            metadata.append(gettext("answered"))
        elif int(comments) > 1:
            metadata.append(status)

        result = {
            'url': url,
            'title': html.unescape(result['title']),
            'content': html.unescape(post.get('blurb', '')),
            'metadata': ' | '.join(metadata),
            'publishedDate': publishedDate,
            'upstream': {'topics': result},
        }

        avatar = post.get('avatar_template', '').replace('{size}', '96')
        if show_avatar and avatar:
            result['thumbnail'] = base_url + avatar

        results.append(result)

    results.append({'number_of_results': len(json_data['topics'])})

    return results
