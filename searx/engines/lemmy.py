# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""This engine uses the Lemmy API (https://lemmy.ml/api/v3/search), which is
documented at `lemmy-js-client`_ / `Interface Search`_.  Since Lemmy is
federated, results are from many different, independent lemmy instances, and not
only the official one.

.. _lemmy-js-client: https://join-lemmy.org/api/modules.html
.. _Interface Search: https://join-lemmy.org/api/interfaces/Search.html

Configuration
=============

The engine has the following additional settings:

- :py:obj:`base_url`
- :py:obj:`lemmy_type`

This implementation is used by different lemmy engines in the :ref:`settings.yml
<settings engine>`:

.. code:: yaml

  - name: lemmy communities
    lemmy_type: Communities
    ...
  - name: lemmy users
    lemmy_type: Users
    ...
  - name: lemmy posts
    lemmy_type: Posts
    ...
  - name: lemmy comments
    lemmy_type: Comments
    ...

Implementations
===============

"""

from datetime import datetime
from urllib.parse import urlencode

from flask_babel import gettext

from searx.utils import markdown_to_text

about = {
    "website": 'https://lemmy.ml/',
    "wikidata_id": 'Q84777032',
    "official_api_documentation": "https://join-lemmy.org/api/",
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}
paging = True
categories = ['social media']

base_url = "https://lemmy.ml/"
"""By default, https://lemmy.ml is used for providing the results.  If you want
to use a different lemmy instance, you can specify ``base_url``.
"""

lemmy_type = "Communities"
"""Any of ``Communities``, ``Users``, ``Posts``, ``Comments``"""


def request(query, params):
    args = {
        'q': query,
        'page': params['pageno'],
        'type_': lemmy_type,
    }

    params['url'] = f"{base_url}api/v3/search?{urlencode(args)}"
    return params


def _get_communities(json):
    results = []

    for result in json["communities"]:
        counts = result['counts']
        metadata = (
            f"{gettext('subscribers')}: {counts.get('subscribers', 0)}"
            f" | {gettext('posts')}: {counts.get('posts', 0)}"
            f" | {gettext('active users')}: {counts.get('users_active_half_year', 0)}"
        )
        results.append(
            {
                'url': result['community']['actor_id'],
                'title': result['community']['title'],
                'content': markdown_to_text(result['community'].get('description', '')),
                'img_src': result['community'].get('icon', result['community'].get('banner')),
                'publishedDate': datetime.strptime(counts['published'][:19], '%Y-%m-%dT%H:%M:%S'),
                'metadata': metadata,
            }
        )
    return results


def _get_users(json):
    results = []

    for result in json["users"]:
        results.append(
            {
                'url': result['person']['actor_id'],
                'title': result['person']['name'],
                'content': markdown_to_text(result['person'].get('bio', '')),
            }
        )

    return results


def _get_posts(json):
    results = []

    for result in json["posts"]:
        user = result['creator'].get('display_name', result['creator']['name'])

        img_src = None
        if result['post'].get('thumbnail_url'):
            img_src = result['post']['thumbnail_url'] + '?format=webp&thumbnail=208'

        metadata = (
            f"&#x25B2; {result['counts']['upvotes']} &#x25BC; {result['counts']['downvotes']}"
            f" | {gettext('user')}: {user}"
            f" | {gettext('comments')}: {result['counts']['comments']}"
            f" | {gettext('community')}: {result['community']['title']}"
        )

        content = result['post'].get('body', '').strip()
        if content:
            content = markdown_to_text(content)

        results.append(
            {
                'url': result['post']['ap_id'],
                'title': result['post']['name'],
                'content': content,
                'img_src': img_src,
                'publishedDate': datetime.strptime(result['post']['published'][:19], '%Y-%m-%dT%H:%M:%S'),
                'metadata': metadata,
            }
        )

    return results


def _get_comments(json):
    results = []

    for result in json["comments"]:
        user = result['creator'].get('display_name', result['creator']['name'])

        content = result['comment'].get('content', '').strip()
        if content:
            content = markdown_to_text(content)

        metadata = (
            f"&#x25B2; {result['counts']['upvotes']} &#x25BC; {result['counts']['downvotes']}"
            f" | {gettext('user')}: {user}"
            f" | {gettext('community')}: {result['community']['title']}"
        )

        results.append(
            {
                'url': result['comment']['ap_id'],
                'title': result['post']['name'],
                'content': markdown_to_text(result['comment']['content']),
                'publishedDate': datetime.strptime(result['comment']['published'][:19], '%Y-%m-%dT%H:%M:%S'),
                'metadata': metadata,
            }
        )

    return results


def response(resp):
    json = resp.json()

    if lemmy_type == "Communities":
        return _get_communities(json)

    if lemmy_type == "Users":
        return _get_users(json)

    if lemmy_type == "Posts":
        return _get_posts(json)

    if lemmy_type == "Comments":
        return _get_comments(json)

    raise ValueError(f"Unsupported lemmy type: {lemmy_type}")
