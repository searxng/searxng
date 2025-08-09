# SPDX-License-Identifier: AGPL-3.0-or-later
"""`Repology`_. `Repology`_ monitors a huge number of package repositories and
other sources comparing packages versions across them and gathering other
information. Repology shows you in which repositories a given project is
packaged, which version is the latest and which needs updating, who maintains
the package, and other related information.

.. _About Repology: https://repology.org/docs/about

"""

import typing

from urllib.parse import urlencode
from searx.utils import searxng_useragent

about = {
    'website': 'https://repology.org',
    'wikidata_id': 'Q107409859',
    'use_official_api': True,
    'official_api_documentation': 'https://repology.org/api/v1',
    'require_api_key': False,
    'results': 'JSON',
}
categories = ['packages', 'it']

base_url = "https://repology.org"


def request(query, params):
    args = {
        'search': query,
    }
    params['headers']['User-Agent'] = searxng_useragent()
    params['url'] = f"{base_url}/api/v1/projects/?{urlencode(args)}"
    return params


def _get_most_common(items: typing.List[typing.Optional[str]]) -> typing.Optional[str]:
    counts = {}
    for item in items:
        if item:
            counts[item] = counts.get(item, 0) + 1

    if len(counts) == 0:
        return None
    return max(counts, key=counts.get)


def _flatten(xss):
    return [x for xs in xss for x in xs]


def response(resp):
    results = []

    resp_json = resp.json()
    for pkgname, repositories in resp_json.items():

        # either there's a package with status "newest"
        # or we assume that the most commonly used version
        # is the latest released (non-alpha) version
        latest_version = None
        for repo in repositories:
            if repo.get("status") == "newest":
                latest_version = repo["version"]
                break
        else:
            latest_version = _get_most_common([repo.get("version") for repo in repositories])

        results.append(
            {
                'template': 'packages.html',
                'url': f"{base_url}/project/{pkgname}/versions",
                'title': pkgname,
                'content': _get_most_common([pkg.get("summary") for pkg in repositories]),
                'package_name': _get_most_common([pkg.get("visiblename") for pkg in repositories]),
                'version': latest_version,
                'license_name': _get_most_common(_flatten([pkg.get("licenses", []) for pkg in repositories])),
                'tags': list({pkg.get("repo") for pkg in repositories}),  # ensure that tags are unique
            }
        )

    return results
