#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""This script saves `Ahmia's blacklist`_ for onion sites.

Output file: :origin:`zhensa/data/ahmia_blacklist.txt` (:origin:`CI Update data
...  <.github/workflows/data-update.yml>`).

.. _Ahmia's blacklist: https://ahmia.fi/blacklist/

"""
# pylint: disable=use-dict-literal

import requests
from zhensa.data import data_dir

DATA_FILE = data_dir / 'ahmia_blacklist.txt'
URL = 'https://ahmia.fi/blacklist/banned/'


def fetch_ahmia_blacklist():
    resp = requests.get(URL, timeout=3.0)
    if resp.status_code != 200:
        # pylint: disable=broad-exception-raised
        raise Exception("Error fetching Ahmia blacklist, HTTP code " + resp.status_code)  # type: ignore
    return resp.text.split()


if __name__ == '__main__':
    blacklist = fetch_ahmia_blacklist()
    blacklist.sort()
    with DATA_FILE.open("w", encoding='utf-8') as f:
        f.write('\n'.join(blacklist))
