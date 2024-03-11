# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=invalid-name
"""Dummy Offline

"""


# about
about = {
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}


def search(query, request_params):  # pylint: disable=unused-argument
    return [
        {
            'result': 'this is what you get',
        }
    ]
