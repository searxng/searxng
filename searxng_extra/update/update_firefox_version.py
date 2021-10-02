#!/usr/bin/env python

import json
import requests
import re
from os.path import dirname, join
from urllib.parse import urlparse, urljoin
from distutils.version import LooseVersion, StrictVersion
from lxml import html
from searx import searx_dir

URL = 'https://ftp.mozilla.org/pub/firefox/releases/'
RELEASE_PATH = '/pub/firefox/releases/'

NORMAL_REGEX = re.compile('^[0-9]+\.[0-9](\.[0-9])?$')
# BETA_REGEX = re.compile('.*[0-9]b([0-9\-a-z]+)$')
# ESR_REGEX = re.compile('^[0-9]+\.[0-9](\.[0-9])?esr$')

# 
useragents = {
    "versions": (),
    "os": ('Windows NT 10.0; WOW64',
           'X11; Linux x86_64'),
    "ua": "Mozilla/5.0 ({os}; rv:{version}) Gecko/20100101 Firefox/{version}"
}


def fetch_firefox_versions():
    resp = requests.get(URL, timeout=2.0)
    if resp.status_code != 200:
        raise Exception("Error fetching firefox versions, HTTP code " + resp.status_code)
    else:
        dom = html.fromstring(resp.text)
        versions = []

        for link in dom.xpath('//a/@href'):
            url = urlparse(urljoin(URL, link))
            path = url.path
            if path.startswith(RELEASE_PATH):
                version = path[len(RELEASE_PATH):-1]
                if NORMAL_REGEX.match(version):
                    versions.append(LooseVersion(version))

        list.sort(versions, reverse=True)
        return versions


def fetch_firefox_last_versions():
    versions = fetch_firefox_versions()

    result = []
    major_last = versions[0].version[0]
    major_list = (major_last, major_last - 1)
    for version in versions:
        major_current = version.version[0]
        if major_current in major_list:
            result.append(version.vstring)

    return result


def get_useragents_filename():
    return join(join(searx_dir, "data"), "useragents.json")


useragents["versions"] = fetch_firefox_last_versions()
with open(get_useragents_filename(), "w") as f:
    json.dump(useragents, f, indent=4, ensure_ascii=False)
