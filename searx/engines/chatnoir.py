# SPDX-License-Identifier: AGPL-3.0-or-later
"""Chatnoir is an open source search engine developed by Webis, a network of
researchers from the universities of Weimar, Halle and Leipzig. It supports
different different text corpora as indexes, e.g. CommonCrawl. See its
`announcement`_ for more information.

.. _announcement : https://groups.google.com/g/common-crawl/c/3o2dOHpeRxo/m/H2Osqz9dAAAJ
"""

import typing as t

from searx.exceptions import SearxEngineAPIException
from searx.extended_types import SXNG_Response
from searx.network import get, post
from searx.result_types import EngineResults
from searx.utils import html_to_text

if t.TYPE_CHECKING:
    from searx.search.processors import OnlineParams

about = {
    "website": "https://www.chatnoir.eu",
    "official_api_documentation": "https://www.chatnoir.eu/docs/api-general",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

base_url = "https://www.chatnoir.eu"
categories = ["general"]

paging = True
page_size = 10

api_key = ""
"""You can optionally provide your own API key here. This one will then be used
instead of scraping an API key."""

search_index = "cw22"
"""Search index to browse in. See `the API documentation
<https://www.chatnoir.eu/docs/api-general>`_ for a full list."""


def _obtain_api_key() -> tuple[str, str, str]:
    home_resp = get(base_url)
    if not home_resp.ok:
        raise SearxEngineAPIException("failed to obtain api key")
    csrf_token = home_resp.cookies["csrftoken"]

    token_resp = post(
        "https://www.chatnoir.eu/?init",
        headers={
            "Referer": f"{base_url}/",
            "X-Requested-With": "XMLHttpRequest",
            "X-Csrf-Token": csrf_token,
        },
        cookies=home_resp.cookies,
    )
    if not token_resp.ok:
        raise SearxEngineAPIException("failed to obtain api key")
    session_id = token_resp.cookies["sessionid"]
    scraped_api_key = token_resp.json()["token"]["token"]

    return csrf_token, session_id, scraped_api_key


def request(query: str, params: "OnlineParams"):
    if api_key:
        # use user-provided API key instead of scraping one
        headers = {
            "Authorization": f"Bearer {api_key}",
        }

        params["headers"].update(headers)
    else:
        csrf_token, session_id, scraped_api_key = _obtain_api_key()

        headers = {
            "Authorization": f"Bearer {scraped_api_key}",
            "X-Csrf-Token": csrf_token,
        }

        params["headers"].update(headers)
        params["cookies"] = {"csrftoken": session_id, "sessionid": session_id}

    params["url"] = f"{base_url}/api/v1/_search"
    params["method"] = "POST"

    json_data = {
        "query": query,
        "index": [
            search_index,
        ],
        "from": (params["pageno"] - 1) * page_size,
        "size": page_size,
        "_extended_meta": True,
    }
    params["json"] = json_data


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()

    results = resp.json()["results"]

    for result in results:
        res.add(
            res.types.MainResult(
                url=result["target_uri"],
                title=html_to_text(result["title"]),
                content=html_to_text(result["snippet"]),
            )
        )

    return res
