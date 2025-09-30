# SPDX-License-Identifier: AGPL-3.0-or-later
"""Engine to search in collaborative software platforms based on GitLab_ with
the `GitLab REST API`_.

.. _GitLab: https://about.gitlab.com/install/
.. _GitLab REST API: https://docs.gitlab.com/ee/api/

Configuration
=============

The engine has the following mandatory setting:

- :py:obj:`base_url`

Optional settings are:

- :py:obj:`api_path`

.. code:: yaml

  - name: gitlab
    engine: gitlab
    base_url: https://gitlab.com
    shortcut: gl
    about:
      website: https://gitlab.com/
      wikidata_id: Q16639197

  - name: gnome
    engine: gitlab
    base_url: https://gitlab.gnome.org
    shortcut: gn
    about:
      website: https://gitlab.gnome.org
      wikidata_id: Q44316

Implementations
===============

"""

from urllib.parse import urlencode
from dateutil import parser

about = {
    "website": None,
    "wikidata_id": None,
    "official_api_documentation": "https://docs.gitlab.com/ee/api/",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

categories = ['it', 'repos']
paging = True

base_url: str = ""
"""Base URL of the GitLab host."""

api_path: str = 'api/v4/projects'
"""The path the `project API <https://docs.gitlab.com/ee/api/projects.html>`_.

The default path should work fine usually.
"""


def request(query, params):
    args = {'search': query, 'page': params['pageno']}
    params['url'] = f"{base_url}/{api_path}?{urlencode(args)}"

    return params


def response(resp):
    results = []

    for item in resp.json():
        results.append(
            {
                'template': 'packages.html',
                'url': item.get('web_url'),
                'title': item.get('name'),
                'content': item.get('description'),
                'thumbnail': item.get('avatar_url'),
                'package_name': item.get('name'),
                'maintainer': item.get('namespace', {}).get('name'),
                'publishedDate': parser.parse(item.get('last_activity_at') or item.get("created_at")),
                'tags': item.get('tag_list', []),
                'popularity': item.get('star_count'),
                'homepage': item.get('readme_url'),
                'source_code_url': item.get('http_url_to_repo'),
            }
        )

    return results
