# SPDX-License-Identifier: AGPL-3.0-or-later
"""Mastodon_ is an open source alternative to large social media platforms like
Twitter/X, Facebook, ...

Since it's federated and self-hostable, there's a large amount of available
instances, which can be chosen instead by modifying ``base_url``.

We use their official API_ for searching, but unfortunately, their Search API_
forbids pagination without OAuth.

That's why we use tootfinder.ch for finding posts, which doesn't support searching
for users, accounts or other types of content on Mastodon however.

.. _Mastodon: https://mastodon.social
.. _API: https://docs.joinmastodon.org/api/

"""

from urllib.parse import urlencode
from datetime import datetime

about = {
    "website": 'https://joinmastodon.org/',
    "wikidata_id": 'Q27986619',
    "official_api_documentation": 'https://docs.joinmastodon.org/api/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}
categories = ['social media']

base_url = "https://mastodon.social"
mastodon_type = "accounts"

# https://github.com/searxng/searxng/pull/2857#issuecomment-1741713999
page_size = 40


def request(query, params):
    args = {
        'q': query,
        'resolve': 'false',
        'type': mastodon_type,
        'limit': page_size,
    }
    params['url'] = f"{base_url}/api/v2/search?{urlencode(args)}"
    return params


def response(resp):
    results = []

    json = resp.json()

    for result in json[mastodon_type]:
        if mastodon_type == "accounts":
            results.append(
                {
                    'url': result['uri'],
                    'title': result['username'] + f" ({result['followers_count']} followers)",
                    'content': result['note'],
                    'thumbnail': result.get('avatar'),
                    'publishedDate': datetime.strptime(result['created_at'][:10], "%Y-%m-%d"),
                }
            )
        elif mastodon_type == "hashtags":
            uses_count = sum(int(entry['uses']) for entry in result['history'])
            user_count = sum(int(entry['accounts']) for entry in result['history'])
            results.append(
                {
                    'url': result['url'],
                    'title': result['name'],
                    'content': f"Hashtag has been used {uses_count} times by {user_count} different users",
                }
            )
        else:
            raise ValueError(f"Unsupported mastodon type: {mastodon_type}")

    return results
