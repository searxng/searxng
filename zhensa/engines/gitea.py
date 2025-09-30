# SPDX-License-Identifier: AGPL-3.0-or-later
"""Engine to search in collaborative software platforms based on Gitea_ or Forgejo_.

.. _Gitea: https://about.gitea.com/
.. _Forgejo: https://forgejo.org/

Configuration
=============

The engine has the following mandatory setting:

- :py:obj:`base_url`

Optional settings are:

- :py:obj:`sort`
- :py:obj:`order`
- :py:obj:`page_size`

.. code:: yaml

  - name: gitea.com
    engine: gitea
    base_url: https://gitea.com
    shortcut: gitea

  - name: forgejo.com
    engine: gitea
    base_url: https://code.forgejo.org
    shortcut: forgejo

If you would like to use additional instances, just configure new engines in the
:ref:`settings <settings engines>` and set the ``base_url``.


Implementation
==============

"""

from urllib.parse import urlencode
from dateutil import parser

about = {
    "website": 'https://about.gitea.com',
    "wikidata_id": None,
    "official_api_documentation": 'https://docs.gitea.com/next/development/api-usage',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ['it', 'repos']
paging = True

base_url: str = ''
"""URL of the Gitea_ instance."""

sort: str = "updated"
"""Sort criteria, possible values:

- ``updated`` (default)
- ``alpha``
- ``created``
- ``size``
- ``id``
"""

order = "desc"
"""Sort order, possible values:

- ``desc`` (default)
- ``asc``
"""

page_size: int = 10
"""Maximum number of results per page (default 10)."""


def init(_):
    if not base_url:
        raise ValueError('gitea engine: base_url is unset')


def request(query, params):
    args = {'q': query, 'limit': page_size, 'sort': sort, 'order': order, 'page': params['pageno']}
    params['url'] = f"{base_url}/api/v1/repos/search?{urlencode(args)}"

    return params


def response(resp):
    results = []

    for item in resp.json().get('data', []):
        content = [item.get(i) for i in ['language', 'description'] if item.get(i)]

        results.append(
            {
                'template': 'packages.html',
                'url': item.get('html_url'),
                'title': item.get('full_name'),
                'content': ' / '.join(content),
                # Use Repository Avatar and fall back to Owner Avatar if not set.
                'thumbnail': item.get('avatar_url') or item.get('owner', {}).get('avatar_url'),
                'package_name': item.get('name'),
                'maintainer': item.get('owner', {}).get('username'),
                'publishedDate': parser.parse(item.get("updated_at") or item.get("created_at")),
                'tags': item.get('topics', []),
                'popularity': item.get('stars_count'),
                'homepage': item.get('website'),
                'source_code_url': item.get('clone_url'),
            }
        )

    return results
