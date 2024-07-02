# SPDX-License-Identifier: AGPL-3.0-or-later
"""`Alpine Linux binary packages`_.  `Alpine Linux`_ is a Linux-based operation
system designed to be small, simple and secure.  Contrary to many other Linux
distributions, it uses musl, BusyBox and OpenRC.  Alpine is mostly used on
servers and for Docker images.

.. _Alpine Linux binary packages: https://pkgs.alpinelinux.org
.. _Alpine Linux: https://www.alpinelinux.org

"""

import re

from urllib.parse import urlencode
from lxml import html
from dateutil import parser

from searx.utils import eval_xpath, eval_xpath_list, extract_text

about = {
    'website': 'https://www.alpinelinux.org',
    'wikidata_id': 'Q4033826',
    'use_official_api': False,
    'official_api_documentation': None,
    'require_api_key': False,
    'results': 'HTML',
}
paging = True
categories = ['packages', 'it']

base_url = "https://pkgs.alpinelinux.org"
alpine_arch = 'x86_64'
"""Kernel architecture: ``x86_64``, ``x86``, ``aarch64``, ``armhf``,
``ppc64le``, ``s390x``, ``armv7`` or ``riscv64``"""

ARCH_RE = re.compile("x86_64|x86|aarch64|armhf|ppc64le|s390x|armv7|riscv64")
"""Regular expression to match supported architectures in the query string."""


def request(query, params):
    query_arch = ARCH_RE.search(query)
    if query_arch:
        query_arch = query_arch.group(0)
        query = query.replace(query_arch, '').strip()

    args = {
        # use wildcards to match more than just packages with the exact same
        # name as the query
        'name': f"*{query}*",
        'page': params['pageno'],
        'arch': query_arch or alpine_arch,
    }
    params['url'] = f"{base_url}/packages?{urlencode(args)}"
    return params


def response(resp):
    results = []

    doc = html.fromstring(resp.text)
    for result in eval_xpath_list(doc, "//table/tbody/tr"):

        if len(result.xpath("./td")) < 9:
            # skip non valid entries in the result table
            # e.g the "No item found..." message
            continue

        results.append(
            {
                'template': 'packages.html',
                'url': base_url + extract_text(eval_xpath(result, './td[contains(@class, "package")]/a/@href')),
                'title': extract_text(eval_xpath(result, './td[contains(@class, "package")]')),
                'package_name': extract_text(eval_xpath(result, './td[contains(@class, "package")]')),
                'publishedDate': parser.parse(extract_text(eval_xpath(result, './td[contains(@class, "bdate")]'))),
                'version': extract_text(eval_xpath(result, './td[contains(@class, "version")]')),
                'homepage': extract_text(eval_xpath(result, './td[contains(@class, "url")]/a/@href')),
                'maintainer': extract_text(eval_xpath(result, './td[contains(@class, "maintainer")]')),
                'license_name': extract_text(eval_xpath(result, './td[contains(@class, "license")]')),
                'tags': [extract_text(eval_xpath(result, './td[contains(@class, "repo")]'))],
            }
        )

    return results
