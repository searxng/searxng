# SPDX-License-Identifier: AGPL-3.0-or-later
"""Engine to search in EDGAR_, the filing system of the U.S. Securities and
Exchange Commission (SEC).  Companies and others are required by U.S. law to
submit documents like annual reports (10-K), quarterly reports (10-Q),
prospectuses (S-1) or current reports (8-K) to this system.

The engine queries EDGAR's full-text search system (EFTS_), which covers all
electronically filed documents since 2001.

.. _EDGAR: https://www.sec.gov/search-filings
.. _EFTS: https://efts.sec.gov/LATEST/search-index?q=%22annual+report%22

Configuration
=============

You can configure the following setting:

- :py:obj:`sec_edgar_forms`

.. code:: yaml

  - name: sec edgar
    engine: sec_edgar
    shortcut: sec
    # limit results to a comma separated list of EDGAR form types
    # sec_edgar_forms: "10-K,10-Q,8-K"

The SEC asks automated tools to identify themselves in the ``User-Agent``
header (`SEC Webmaster FAQ`_).  The engine sends SearXNG's own user agent
(:py:obj:`searx.utils.searxng_useragent`); contact information can be added
with the ``useragent_suffix`` setting:

.. code:: yaml

  outgoing:
    useragent_suffix: "admin@example.org"

.. _SEC Webmaster FAQ: https://www.sec.gov/os/webmaster-faq#developers

Implementations
===============

"""

import re
import typing as t

from datetime import datetime, timedelta
from urllib.parse import urlencode

from searx.utils import searxng_useragent
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://www.sec.gov/search-filings",
    "wikidata_id": "Q3050604",
    "official_api_documentation": "https://www.sec.gov/search-filings/edgar-application-programming-interfaces",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

categories = ["general"]
paging = True
page_size = 100
"""EFTS always returns 100 hits per request."""

max_page = 100
"""EFTS rejects requests with an offset beyond 10.000 hits."""

time_range_support = True
time_range_days = {"day": 1, "week": 7, "month": 30, "year": 365}

base_url: str = "https://efts.sec.gov/LATEST/search-index"
"""URL of the EFTS (JSON API)."""

archive_url: str = "https://www.sec.gov/Archives/edgar/data"
"""URL under which the filed documents are archived."""

sec_edgar_forms: str = ""
"""Optional comma separated list of `EDGAR form types`_ to limit the results
to, e.g. ``10-K,10-Q,8-K``.  By default, all form types are searched.

.. _EDGAR form types: https://www.sec.gov/forms
"""

_cik_re = re.compile(r"\s*\(CIK\s+\d+\)\s*$")


def request(query: str, params: "OnlineParams") -> None:

    args: dict[str, str | int] = {"q": query}
    if sec_edgar_forms:
        args["forms"] = sec_edgar_forms
    if params["time_range"]:
        start = datetime.now() - timedelta(days=time_range_days[params["time_range"]])
        args["dateRange"] = "custom"
        args["startdt"] = start.strftime("%Y-%m-%d")
        args["enddt"] = datetime.now().strftime("%Y-%m-%d")
    if params["pageno"] > 1:
        args["from"] = (params["pageno"] - 1) * page_size

    params["url"] = f"{base_url}?{urlencode(args)}"
    # the SEC's fair access policy asks automated tools to identify themselves
    params["headers"]["User-Agent"] = searxng_useragent()
    params["headers"]["Accept"] = "application/json"


def response(resp: "SXNG_Response") -> EngineResults:

    res = EngineResults()

    for hit in (resp.json().get("hits") or {}).get("hits") or []:
        src = hit.get("_source") or {}
        adsh: str = src.get("adsh") or ""
        ciks: list[str] = src.get("ciks") or []
        _, _, file_name = (hit.get("_id") or "").partition(":")
        if not (adsh and ciks and file_name):
            continue

        # the primary documents of some form types (e.g. ownership statements)
        # are XML files, for which EDGAR serves a rendered version under the
        # path of their XSL stylesheet
        path = [ciks[0].lstrip("0"), adsh.replace("-", "")]
        if src.get("xsl"):
            path.append(src["xsl"])
        path.append(file_name)

        form: str = src.get("form") or src.get("file_type") or ""
        company: str = " ".join(_cik_re.sub("", (src.get("display_names") or [""])[0]).split())
        title = ": ".join(x for x in (form, company) if x) or adsh

        content_parts: list[str] = []
        description: str = src.get("file_description") or ""
        if description and description != form:
            content_parts.append(description)
        if src.get("period_ending"):
            content_parts.append(f"Period ending {src['period_ending']}")
        if src.get("biz_locations"):
            content_parts.append(src["biz_locations"][0])

        published_date = None
        if src.get("file_date"):
            try:
                published_date = datetime.strptime(src["file_date"], "%Y-%m-%d")
            except ValueError:
                pass

        res.add(
            res.types.MainResult(
                url=f"{archive_url}/{'/'.join(path)}",
                title=title,
                content=" | ".join(content_parts),
                publishedDate=published_date,
            )
        )

    return res
