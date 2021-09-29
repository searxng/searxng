# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Dummy
"""

# about
about = {
    "website": None,
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'empty array',
}


# do search-request
def request(query, params):
    return params


# get response from search-request
def response(resp):
    return []
