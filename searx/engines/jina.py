# SPDX-License-Identifier: AGPL-3.0-or-later
"""Jina is a search AI and part of Elastic, the company behind ElasticSearch.

The engine requires an API key, you can get one from the
`API dashboard <https://jina.ai/api-dashboard/>`_ without signup.

.. code:: yaml

  - name: jina
    engine: jina
    shortcut: ji
    api_key: "jina_..."
    jina_engine: reader
    inactive: false

By default, Jina's own index is used. You can change that by setting a different :py:obj:`jina_engine`.
"""

import typing as t
from urllib.parse import urlencode

from dateutil import parser
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://jina.ai",
    "wikidata_id": None,
    "official_api_documentation": "https://s.jina.ai/docs",
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
}

categories = ["general"]
paging = True

jina_engine = "reader"
"""Search mode. Currently supported values are 'reader', 'google' and 'bing'."""

base_url = "https://s.jina.ai"
api_key: str | None = None


def setup(_):
    if not api_key:
        raise ValueError("missing api key")


def request(query: str, params: "OnlineParams"):
    # setting 'no-content' pushes the response time down to a third
    args = {"q": query, "page": params["pageno"], "engine": jina_engine, "respondWith": "no-content"}
    params["url"] = f"{base_url}/?{urlencode(args)}"
    params["headers"].update(
        {
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
    )


def response(resp: "SXNG_Response"):
    res = EngineResults()

    json_resp: dict[str, t.Any] = resp.json()

    result: dict[str, str]
    for result in json_resp["data"]:
        published_date = None
        if result.get("date"):
            try:
                published_date = parser.parse(result["date"])
            except parser.ParserError:
                pass

        res.add(
            res.types.MainResult(
                url=result["url"],
                title=result["title"],
                content=result["description"],
                publishedDate=published_date,
            )
        )

    return res
