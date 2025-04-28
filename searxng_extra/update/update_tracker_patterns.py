# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fetch trackers"""

import json
import httpx

from searx.data import data_dir

DATA_FILE = data_dir / "tracker_patterns.json"
CLEAR_LIST_URL = "https://raw.githubusercontent.com/ClearURLs/Rules/refs/heads/master/data.min.json"


def fetch_clear_url_filters():
    resp = httpx.get(CLEAR_LIST_URL)
    if resp.status_code != 200:
        # pylint: disable=broad-exception-raised
        raise Exception(f"Error fetching ClearURL filter lists, HTTP code {resp.status_code}")

    providers = resp.json()["providers"]
    rules = []
    for rule in providers.values():
        rules.append(
            {
                "urlPattern": rule["urlPattern"].replace("\\\\", "\\"),  # fix javascript regex syntax
                "exceptions": [exc.replace("\\\\", "\\") for exc in rule["exceptions"]],
                "trackerParams": rule["rules"],
            }
        )

    return rules


if __name__ == '__main__':
    filter_list = fetch_clear_url_filters()
    with DATA_FILE.open("w", encoding='utf-8') as f:
        json.dump(filter_list, f, indent=4, sort_keys=True, ensure_ascii=False)
