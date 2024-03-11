# SPDX-License-Identifier: AGPL-3.0-or-later
"""Hackernews
"""

from datetime import datetime
from urllib.parse import urlencode
from dateutil.relativedelta import relativedelta

from flask_babel import gettext

# Engine metadata
about = {
    "website": "https://news.ycombinator.com/",
    "wikidata_id": "Q686797",
    "official_api_documentation": "https://hn.algolia.com/api",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

# Engine configuration
paging = True
time_range_support = True
categories = ["it"]
results_per_page = 30

# Search URL
base_url = "https://hn.algolia.com/api/v1"


def request(query, params):
    search_type = 'search'
    if not query:
        # if search query is empty show results from HN's front page
        search_type = 'search_by_date'
        query_params = {
            "tags": "front_page",
            "page": (params["pageno"] - 1),
        }
    else:
        query_params = {
            "query": query,
            "page": (params["pageno"] - 1),
            "hitsPerPage": results_per_page,
            "minWordSizefor1Typo": 4,
            "minWordSizefor2Typos": 8,
            "advancedSyntax": "true",
            "ignorePlurals": "false",
            "minProximity": 7,
            "numericFilters": '[]',
            "tagFilters": '["story",[]]',
            "typoTolerance": "true",
            "queryType": "prefixLast",
            "restrictSearchableAttributes": '["title","comment_text","url","story_text","author"]',
            "getRankingInfo": "true",
        }

        if params['time_range']:
            search_type = 'search_by_date'
            timestamp = (datetime.now() - relativedelta(**{f"{params['time_range']}s": 1})).timestamp()
            query_params["numericFilters"] = f"created_at_i>{timestamp}"

    params["url"] = f"{base_url}/{search_type}?{urlencode(query_params)}"
    return params


def response(resp):
    results = []
    data = resp.json()

    for hit in data["hits"]:
        object_id = hit["objectID"]
        points = hit.get("points") or 0
        num_comments = hit.get("num_comments") or 0

        metadata = ""
        if points != 0 or num_comments != 0:
            metadata = f"{gettext('points')}: {points}" f" | {gettext('comments')}: {num_comments}"
        results.append(
            {
                "title": hit.get("title") or f"{gettext('author')}: {hit['author']}",
                "url": f"https://news.ycombinator.com/item?id={object_id}",
                "content": hit.get("url") or hit.get("comment_text") or hit.get("story_text") or "",
                "metadata": metadata,
                "author": hit["author"],
                "publishedDate": datetime.utcfromtimestamp(hit["created_at_i"]),
            }
        )

    return results
