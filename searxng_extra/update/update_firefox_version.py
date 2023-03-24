#!/usr/bin/env python
# lint: pylint
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fetch firefox useragent signatures

Output file: :origin:`searx/data/useragents.json` (:origin:`CI Update data ...
<.github/workflows/data-update.yml>`).

"""
# pylint: disable=use-dict-literal

import json
import re
from os.path import join
from urllib.parse import urlparse, urljoin
from packaging.version import parse

import requests
from lxml import html
from searx import searx_dir

URL = 'https://ftp.mozilla.org/pub/firefox/releases/'
RELEASE_PATH = '/pub/firefox/releases/'

NORMAL_REGEX = re.compile(r'^[0-9]+\.[0-9](\.[0-9])?$')
# BETA_REGEX = re.compile(r'.*[0-9]b([0-9\-a-z]+)$')
# ESR_REGEX = re.compile(r'^[0-9]+\.[0-9](\.[0-9])?esr$')

#
useragents = {
    # fmt: off
    "versions": (),
    "os": ('Windows NT 10.0; Win64; x64',
           'X11; Linux x86_64'),
    "ua": "Mozilla/5.0 ({os}; rv:{version}) Gecko/20100101 Firefox/{version}",
    # fmt: on
}


def fetch_firefox_versions():
    resp = requests.get(URL, timeout=2.0)
    if resp.status_code != 200:
        # pylint: disable=broad-exception-raised
        raise Exception("Error fetching firefox versions, HTTP code " + resp.status_code)
    dom = html.fromstring(resp.text)
    versions = []

    for link in dom.xpath('//a/@href'):
        url = urlparse(urljoin(URL, link))
        path = url.path
        if path.startswith(RELEASE_PATH):
            version = path[len(RELEASE_PATH) : -1]
            if NORMAL_REGEX.match(version):
                versions.append(parse(version))

    list.sort(versions, reverse=True)
    return versions


def fetch_firefox_last_versions():
    versions = fetch_firefox_versions()

    result = []
    major_last = versions[0].major
    major_list = (major_last, major_last - 1)
    for version in versions:
        major_current = version.major
        minor_current = version.minor
        if major_current in major_list:
            user_agent_version = f'{major_current}.{minor_current}'
            if user_agent_version not in result:
                result.append(user_agent_version)

    return result


def get_useragents_filename():
    return join(join(searx_dir, "data"), "useragents.json")


if __name__ == '__main__':
    useragents["versions"] = fetch_firefox_last_versions()
    with open(get_useragents_filename(), "w", encoding='utf-8') as f:
        json.dump(useragents, f, indent=4, ensure_ascii=False)
