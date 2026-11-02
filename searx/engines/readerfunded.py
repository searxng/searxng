# SPDX-License-Identifier: AGPL-3.0-or-later
"""ReaderFunded_ is an independent web search engine with its own index. A
site is indexed only when its readers support it with their own money: a
link from the site to its page on Patreon, Ko-fi, Substack, GitHub
Sponsors, Open Collective, Liberapay or a similar platform, and that page
naming the site back, verified in both directions and re-checked monthly.
A site ranks higher the more readers pay for it, text relevance first.

The engine uses the public `JSON API`_ which doesn't require an API key.
This allows to run 120 requests per minute. If that doesn't suffice for you, you can
obtain a free API key `here <https://readerfunded.com/api#keys>`_.

.. code:: yaml

   - name: readerfunded
     engine: readerfunded
     shortcut: rfd
     api_key: ""  # optional

.. _ReaderFunded: https://readerfunded.com
.. _JSON API: https://readerfunded.com/api
"""

import typing as t
from datetime import datetime
from urllib.parse import urlencode

from searx.exceptions import SearxEngineResponseException
from searx.utils import searxng_useragent
from searx.result_types import EngineResults
from searx.extended_types import SXNG_Response

about = {
    "website": "https://readerfunded.com",
    "wikidata_id": None,
    "official_api_documentation": "https://readerfunded.com/api",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

categories = ["general", "web"]
paging = False
time_range_support = True

base_url = "https://readerfunded.com"
page_size = 20
api_key: str = ""
"""Optional.  A key from https://readerfunded.com/api#keys gives the instance
an allowance of its own instead of the one every SearXNG instance behind
its address shares."""

time_range_map = {"day": "day", "week": "week", "month": "month", "year": "year"}


def request(query: str, params: dict[str, t.Any]) -> None:

    args: dict[str, t.Any] = {"q": query, "top": page_size}
    if params.get("time_range") in time_range_map:
        args["t"] = time_range_map[params["time_range"]]
    # the API takes a two-letter language preferred first beside English;
    # ``all`` is no preference
    locale = str(params.get("searxng_locale") or params.get("language") or "all")
    lang = locale.split("-", maxsplit=1)[0].lower()
    args["lang"] = lang if lang and lang != "auto" else "all"

    params["url"] = f"{base_url}/api/search?{urlencode(args)}"
    params["headers"]["Accept"] = "application/json"
    # the API asks callers to say who they are, and gives a SearXNG instance
    # a larger keyless allowance than an anonymous address when it does
    params["headers"]["User-Agent"] = searxng_useragent()
    if api_key:
        params["headers"]["X-Api-Key"] = api_key


def _published(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def response(resp: SXNG_Response) -> EngineResults:

    res = EngineResults()
    resp_json = resp.json()
    if resp_json.get("timed_out"):
        raise SearxEngineResponseException("timeout")

    for item in resp_json.get("results", []):
        url = item.get("url")
        if not url:
            continue
        res.add(
            res.types.MainResult(
                url=url,
                title=item.get("title") or url,
                content=item.get("snippet") or "",
                publishedDate=_published(item.get("published")),
            )
        )

    suggestion = resp_json.get("did_you_mean")
    if suggestion:
        res.add(res.types.LegacyResult(suggestion=suggestion))

    return res
