# SPDX-License-Identifier: AGPL-3.0-or-later
"""Google Scholar is a freely accessible web search engine that indexes the full
text or metadata of scholarly literature across an array of publishing formats
and disciplines.

Compared to other Google services the Scholar engine has a simple GET REST-API
and there does not exists ``async`` API.  Even though the API slightly vintage
we can make use of the :ref:`google API` to assemble the arguments of the GET
request.

Configuration
=============

.. code:: yaml

  - name: google scholar
    engine: google_scholar
    shortcut: gos

Implementations
===============

"""

import typing as t

from urllib.parse import urlencode
from datetime import datetime
from lxml import html
import httpx

from searx.utils import (
    eval_xpath,
    eval_xpath_getindex,
    eval_xpath_list,
    extract_text,
    ElementType,
)

from searx.exceptions import SearxEngineCaptchaException, SearxEngineAccessDeniedException

from searx.engines.google import fetch_traits  # pylint: disable=unused-import
from searx.engines.google import (
    get_google_info,
    time_range_dict,
)

from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://scholar.google.com",
    "wikidata_id": "Q494817",
    "official_api_documentation": "https://developers.google.com/custom-search",
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

# engine dependent config
categories = ["science", "scientific publications"]
paging = True
max_page = 50
"""`Google max 50 pages`_

.. _Google max 50 pages: https://github.com/searxng/searxng/issues/2982
"""
language_support = True
time_range_support = True
safesearch = False
send_accept_language_header = True


def request(query: str, params: "OnlineParams") -> None:
    """Google-Scholar search request"""

    google_info = get_google_info(params, traits)
    # subdomain is: scholar.google.xy
    google_info["subdomain"] = google_info["subdomain"].replace("www.", "scholar.")

    args = {
        "q": query,
        **google_info["params"],
        "start": (params["pageno"] - 1) * 10,
        "as_sdt": "2007",  # include patents / to disable set "0,5"
        "as_vis": "0",  # include citations / to disable set "1"
    }
    args.update(time_range_args(params))

    params["url"] = "https://" + google_info["subdomain"] + "/scholar?" + urlencode(args)
    params["cookies"] = google_info["cookies"]
    params["headers"].update(google_info["headers"])


def response(resp: "SXNG_Response") -> EngineResults:  # pylint: disable=too-many-locals
    """Parse response from Google Scholar"""

    if resp.status_code in (301, 302, 303, 307, 308) and "Location" in resp.headers:
        if "/sorry/index?continue" in resp.headers["Location"]:
            # Our systems have detected unusual traffic from your computer
            # network. Please try again later.
            raise SearxEngineAccessDeniedException(
                message="google_scholar: unusual traffic detected",
            )
        raise httpx.TooManyRedirects(f"location {resp.headers['Location'].split('?')[0]}")

    res = EngineResults()
    dom = html.fromstring(resp.text)
    detect_google_captcha(dom)

    # parse results
    for result in eval_xpath_list(dom, "//div[@data-rp]"):

        title = extract_text(eval_xpath(result, ".//h3[1]//a"))
        if not title:
            # this is a [ZITATION] block
            continue

        pub_type: str = extract_text(eval_xpath(result, ".//span[@class='gs_ctg2']")) or ""
        if pub_type:
            pub_type = pub_type[1:-1].lower()

        url: str = eval_xpath_getindex(result, ".//h3[1]//a/@href", 0)
        content: str = extract_text(eval_xpath(result, ".//div[@class='gs_rs']")) or ""
        authors, journal, publisher, publishedDate = parse_gs_a(
            extract_text(eval_xpath(result, ".//div[@class='gs_a']"))
        )
        if publisher in url:
            publisher = ""

        # cited by
        comments: str = (
            extract_text(eval_xpath(result, ".//div[@class='gs_fl']/a[starts-with(@href,'/scholar?cites=')]")) or ""
        )

        # link to the html or pdf document
        html_url: str = ""
        pdf_url: str = ""
        doc_url = eval_xpath_getindex(result, ".//div[@class='gs_or_ggsm']/a/@href", 0, default=None)
        doc_type = extract_text(eval_xpath(result, ".//span[@class='gs_ctg2']"))
        if doc_type == "[PDF]":
            pdf_url = doc_url
        else:
            html_url = doc_url

        res.add(
            res.types.Paper(
                type=pub_type,
                url=url,
                title=title,
                authors=authors,
                publisher=publisher,
                journal=journal,
                publishedDate=publishedDate,
                content=content,
                comments=comments,
                html_url=html_url,
                pdf_url=pdf_url,
            )
        )

    # parse suggestion
    for suggestion in eval_xpath(dom, "//div[contains(@class, 'gs_qsuggest_wrap')]//li//a"):
        res.add(res.types.LegacyResult(suggestion=extract_text(suggestion)))

    for correction in eval_xpath(dom, "//div[@class='gs_r gs_pda']/a"):
        res.add(res.types.LegacyResult(correction=extract_text(correction)))
    return res


def time_range_args(params: "OnlineParams") -> dict[str, int]:
    """Returns a dictionary with a time range arguments based on
    ``params["time_range"]``.

    Google Scholar supports a detailed search by year.  Searching by *last
    month* or *last week* (as offered by SearXNG) is uncommon for scientific
    publications and is not supported by Google Scholar.

    To limit the result list when the users selects a range, all the SearXNG
    ranges (*day*, *week*, *month*, *year*) are mapped to *year*.  If no range
    is set an empty dictionary of arguments is returned.

    Example; when user selects a time range and we find ourselves in the year
    2025 (current year minus one):

    .. code:: python

        { "as_ylo" : 2024 }

    """
    ret_val: dict[str, int] = {}
    if params["time_range"] in time_range_dict:
        ret_val["as_ylo"] = datetime.now().year - 1
    return ret_val


def detect_google_captcha(dom: ElementType):
    """In case of CAPTCHA Google Scholar open its own *not a Robot* dialog and is
    not redirected to ``sorry.google.com``.
    """
    if eval_xpath(dom, "//form[@id='gs_captcha_f']"):
        raise SearxEngineCaptchaException(message="CAPTCHA (gs_captcha_f)")


def parse_gs_a(text: str | None) -> tuple[list[str], str, str, datetime | None]:
    """Parse the text written in green.

    Possible formats:
    * "{authors} - {journal}, {year} - {publisher}"
    * "{authors} - {year} - {publisher}"
    * "{authors} - {publisher}"
    """
    if text is None or text == "":
        return [], "", "", None

    s_text = text.split(" - ")
    authors: list[str] = s_text[0].split(", ")
    publisher: str = s_text[-1]
    if len(s_text) != 3:
        return authors, "", publisher, None

    # the format is "{authors} - {journal}, {year} - {publisher}" or "{authors} - {year} - {publisher}"
    # get journal and year
    journal_year = s_text[1].split(", ")
    # journal is optional and may contains some coma
    if len(journal_year) > 1:
        journal: str = ", ".join(journal_year[0:-1])
        if journal == "…":
            journal = ""
    else:
        journal = ""
    # year
    year = journal_year[-1]
    try:
        publishedDate = datetime.strptime(year.strip(), "%Y")
    except ValueError:
        publishedDate = None
    return authors, journal, publisher, publishedDate
