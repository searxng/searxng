#!/usr/bin/env python
# lint: pylint
# SPDX-License-Identifier: AGPL-3.0-or-later
"""This script saves `Ahmia's blacklist`_ for onion sites.

Output file: :origin:`searx/data/ahmia_blacklist.txt` (:origin:`CI Update data
...  <.github/workflows/data-update.yml>`).

.. _Ahmia's blacklist: https://ahmia.fi/blacklist/

"""

from os.path import join

import requests
from searx import searx_dir

URL = 'https://ahmia.fi/blacklist/banned/'


def fetch_ahmia_blacklist():
    resp = requests.get(URL, timeout=3.0)
    if resp.status_code != 200:
        raise Exception("Error fetching Ahmia blacklist, HTTP code " + resp.status_code)
    return resp.text.split()


def get_ahmia_blacklist_filename():
    return join(join(searx_dir, "data"), "ahmia_blacklist.txt")


if __name__ == '__main__':
    blacklist = fetch_ahmia_blacklist()
    with open(get_ahmia_blacklist_filename(), "w", encoding='utf-8') as f:
        f.write('\n'.join(blacklist))
