# SPDX-License-Identifier: AGPL-3.0-or-later
"""ChinaSo_, a search engine for the chinese language area.

.. attention::

   ChinaSo engine does not return real URL, the links from these search
   engines violate the privacy of the users!!

   We try to find a solution for this problem, please follow `issue #4694`_.

   As long as the problem has not been resolved, these engines are
   not active in a standard setup (``inactive: true``).

.. _ChinaSo: https://www.chinaso.com/
.. _issue #4694: https://github.com/searxng/searxng/issues/4694

Configuration
=============

The engine has the following additional settings:

- :py:obj:`chinaso_news_source` (:py:obj:`ChinasoNewsSourceType`)

In the example below, ChinaSO is configured for news search.

.. code:: yaml

   - name: chinaso news
     engine: chinaso
     shortcut: chinaso
     categories: [news]
     chinaso_news_source: all


Implementations
===============

"""

import typing as t
import base64
import secrets

from urllib.parse import urlencode
from datetime import datetime

from searx.exceptions import SearxEngineAPIException
from searx.utils import html_to_text

about = {
    "website": "https://www.chinaso.com/",
    "wikidata_id": "Q10846064",
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

paging = True
time_range_support = True
results_per_page = 10
categories = []
language = "zh"

ChinasoNewsSourceType = t.Literal['CENTRAL', 'LOCAL', 'BUSINESS', 'EPAPER', 'all']
"""Filtering ChinaSo-News results by source:

- ``CENTRAL``: central publication
- ``LOCAL``: local publication
- ``BUSINESS``: business publication
- ``EPAPER``: E-Paper
- ``all``: all sources
"""
chinaso_news_source: ChinasoNewsSourceType = 'all'
"""Configure ChinaSo-News type (:py:obj:`ChinasoNewsSourceType`)."""

time_range_dict = {'day': '24h', 'week': '1w', 'month': '1m', 'year': '1y'}

base_url = "https://www.chinaso.com"


def init(_):
    if chinaso_news_source not in t.get_args(ChinasoNewsSourceType):
        raise ValueError(f"Unsupported news source: {chinaso_news_source}")


def request(query, params):
    query_params = {'q': query, 'pn': params["pageno"], 'ps': results_per_page}

    if time_range_dict.get(params['time_range']):
        query_params["stime"] = time_range_dict[params['time_range']]
        query_params["etime"] = 'now'

    if chinaso_news_source != 'all':
        if chinaso_news_source == 'EPAPER':
            query_params["type"] = 'EPAPER'
        else:
            query_params["cate"] = chinaso_news_source

    params["url"] = f"{base_url}/v5/general/v1/web/search?{urlencode(query_params)}"
    cookie = {
        "uid": base64.b64encode(secrets.token_bytes(16)).decode("utf-8"),
    }
    params["cookies"] = cookie

    return params


def response(resp):
    try:
        data = resp.json()
    except Exception as e:
        raise SearxEngineAPIException(f"Invalid response: {e}") from e

    # Upstream returns {'status': 0, 'msg': 'empty result', 'data': {}} when there
    # are no results; this is a valid empty result rather than an API error.
    if not isinstance(data, dict) or "data" not in data:
        raise SearxEngineAPIException("Invalid response")
    if not data["data"]:
        return []

    results = []
    if not data.get("data", {}).get("data"):
        raise SearxEngineAPIException("Invalid response")

    for entry in data["data"]["data"]:
        published_date = None
        if entry.get("timestamp"):
            try:
                published_date = datetime.fromtimestamp(int(entry["timestamp"]))
            except (ValueError, TypeError):
                pass

        results.append(
            {
                'title': html_to_text(entry["title"]),
                'url': entry["url"],
                'content': html_to_text(entry["snippet"]),
                'publishedDate': published_date,
            }
        )
    return results
