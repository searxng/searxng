# SPDX-License-Identifier: AGPL-3.0-or-later
"""Repology_ monitors a huge number of package repositories and other sources
comparing packages versions across them and gathering other information.

Repology_ shows you in which repositories a given project is packaged, which
version is the latest and which needs updating, who maintains the package, and
other related information.

.. _Repology: https://repology.org/docs/about

Configuration
=============

The engine is inactive by default, meaning it is not available in the service.
If you want to offer the engine, the ``inactive`` flag must be set to ``false``.

.. code:: yaml

  - name: repology
    inactive: false

"""

import typing as t

from urllib.parse import urlencode
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response

about = {
    'website': 'https://repology.org',
    'wikidata_id': 'Q107409859',
    'use_official_api': True,
    'official_api_documentation': 'https://repology.org/api/v1',
    'require_api_key': False,
    'results': 'JSON',
}
categories: list[str] = ['packages', 'it']
base_url: str = 'https://repology.org'


def request(query: str, params: dict[str, t.Any]) -> None:
    args = {
        'search': query,
    }
    params['url'] = f"{base_url}/api/v1/projects/?{urlencode(args)}"


def _get_most_common(items: list[str | None]) -> str | None:
    counts: dict[str | None, int] = {}
    for item in items:
        if item:
            counts[item] = counts.get(item, 0) + 1

    if len(counts) == 0:
        return None
    return max(counts, key=counts.get)


def _flatten(xss):
    return [x for xs in xss for x in xs]


def response(resp: 'SXNG_Response') -> EngineResults:
    res = EngineResults()

    resp_json = resp.json()
    for pkgname, repositories in resp_json.items():

        # either there's a package with status "newest" or we assume that the
        # most commonly used version is the latest released (non-alpha) version
        latest_version = None
        for repo in repositories:
            if repo.get("status") == "newest":
                latest_version = repo["version"]
                break
        else:
            latest_version = _get_most_common([repo.get("version") for repo in repositories])

        res.add(
            res.types.LegacyResult(
                template='packages.html',
                url=f"{base_url}/project/{pkgname}/versions",
                title=pkgname,
                content=_get_most_common([pkg.get("summary") for pkg in repositories]),
                package_name=_get_most_common([pkg.get("visiblename") for pkg in repositories]),
                version=latest_version,
                license_name=_get_most_common(_flatten([pkg.get("licenses", []) for pkg in repositories])),
                tags=list({pkg.get("repo") for pkg in repositories}),  # ensure that tags are unique
            )
        )

    return res
