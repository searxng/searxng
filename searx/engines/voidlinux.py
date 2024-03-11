# SPDX-License-Identifier: AGPL-3.0-or-later
"""SearXNG engine for `Void Linux binary packages`_.  Void is a general purpose
operating system, based on the monolithic Linux kernel. Its package system
allows you to quickly install, update and remove software; software is provided
in binary packages or can be built directly from sources with the help of the
XBPS source packages collection.

.. _Void Linux binary packages: https://voidlinux.org/packages/

"""

import re

from urllib.parse import quote_plus
from searx.utils import humanize_bytes

about = {
    'website': 'https://voidlinux.org/packages/',
    'wikidata_id': 'Q19310966',
    'use_official_api': True,
    'official_api_documentation': None,
    'require_api_key': False,
    'results': 'JSON',
}

categories = ['packages', 'it']

base_url = "https://xq-api.voidlinux.org"
pkg_repo_url = "https://github.com/void-linux/void-packages"

void_arch = 'x86_64'
"""Default architecture to search for.  For valid values see :py:obj:`ARCH_RE`"""

ARCH_RE = re.compile('aarch64-musl|armv6l-musl|armv7l-musl|x86_64-musl|aarch64|armv6l|armv7l|i686|x86_64')
"""Regular expresion that match a architecture in the query string."""


def request(query, params):
    arch_path = ARCH_RE.search(query)
    if arch_path:
        arch_path = arch_path.group(0)
        query = query.replace(arch_path, '').strip()
    else:
        arch_path = void_arch

    params['url'] = f"{base_url}/v1/query/{arch_path}?q={quote_plus(query)}"
    return params


def response(resp):
    """
    At Void Linux, several packages sometimes share the same source code
    (template) and therefore also have the same URL.  Results with identical
    URLs are merged as one result for SearXNG.
    """

    packages = {}
    for result in resp.json()['data']:

        # 32bit and dbg packages don't have their own package templates
        github_slug = re.sub(r"-(32bit|dbg)$", "", result['name'])
        pkg_url = f"{pkg_repo_url}/tree/master/srcpkgs/{github_slug}"

        pkg_list = packages.get(pkg_url, [])
        pkg_list.append(
            {
                'title': result['name'],
                'content': f"{result['short_desc']} - {humanize_bytes(result['filename_size'])}",
                'package_name': result['name'],
                'version': f"v{result['version']}_{result['revision']}",
                'tags': result['repository'],
            }
        )
        packages[pkg_url] = pkg_list

    results = []
    for pkg_url, pkg_list in packages.items():

        results.append(
            {
                'url': pkg_url,
                'template': 'packages.html',
                'title': ' | '.join(x['title'] for x in pkg_list),
                'content': pkg_list[0]['content'],
                'package_name': ' | '.join(x['package_name'] for x in pkg_list),
                'version': pkg_list[0]['version'],
                'tags': [x['tags'] for x in pkg_list],
            }
        )
    return results
