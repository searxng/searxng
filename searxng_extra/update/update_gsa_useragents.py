#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""This script fetches user agents suitable for Google.

Output file: :origin:`searx/data/gsa_useragents.txt` (:origin:`CI Update data
...  <.github/workflows/data-update.yml>`).

.. Source for user agents: https://github.com/intoli/user-agents/

"""
# pylint: disable=use-dict-literal

from json import loads
from gzip import decompress

from searx.data import data_dir
from searx.utils import searxng_useragent
from searx.network import get as http_get

DATA_FILE = data_dir / 'gsa_useragents.txt'
URL = 'https://raw.githubusercontent.com/intoli/user-agents/main/src/user-agents.json.gz'


def fetch_gsa_useragents() -> list[str]:
    response = http_get(URL, timeout=3.0, headers={"User-Agent": searxng_useragent()})
    response.raise_for_status()

    uas = []
    for ua in loads(decompress(response.content)):
        if ua["platform"] == "iPhone" and "GSA" in ua["userAgent"]:
            uas.append(ua["userAgent"])

    uas.sort()
    return uas


if __name__ == '__main__':
    useragents = fetch_gsa_useragents()
    with DATA_FILE.open("w", encoding='utf-8') as f:
        f.write('\n'.join(useragents))
