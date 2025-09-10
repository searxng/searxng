# SPDX-License-Identifier: AGPL-3.0-or-later
"""arXiv is a free distribution service and an open-access archive for nearly
2.4 million scholarly articles in the fields of physics, mathematics, computer
science, quantitative biology, quantitative finance, statistics, electrical
engineering and systems science, and economics.

The engine uses the `arXiv API`_.

.. _arXiv API: https://info.arxiv.org/help/api/user-manual.html
"""

import typing as t

from datetime import datetime
from urllib.parse import urlencode

from lxml import etree
from lxml.etree import XPath
from searx.utils import eval_xpath, eval_xpath_list, eval_xpath_getindex
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://arxiv.org",
    "wikidata_id": "Q118398",
    "official_api_documentation": "https://info.arxiv.org/help/api/user-manual.html",
    "use_official_api": True,
    "require_api_key": False,
    "results": "XML-RSS",
}

categories = ["science", "scientific publications"]
paging = True
arxiv_max_results = 10
arxiv_search_prefix = "all"
"""Search fields, for more details see, `Details of Query Construction`_.

.. _Details of Query Construction:
   https://info.arxiv.org/help/api/user-manual.html#51-details-of-query-construction
"""

base_url = "https://export.arxiv.org/api/query"
"""`arXiv API`_ URL, for more details see Query-Interface_

.. _Query-Interface: https://info.arxiv.org/help/api/user-manual.html#_query_interface
"""

arxiv_namespaces = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}
xpath_entry = XPath("//atom:entry", namespaces=arxiv_namespaces)
xpath_title = XPath(".//atom:title", namespaces=arxiv_namespaces)
xpath_id = XPath(".//atom:id", namespaces=arxiv_namespaces)
xpath_summary = XPath(".//atom:summary", namespaces=arxiv_namespaces)
xpath_author_name = XPath(".//atom:author/atom:name", namespaces=arxiv_namespaces)
xpath_doi = XPath(".//arxiv:doi", namespaces=arxiv_namespaces)
xpath_pdf = XPath(".//atom:link[@title='pdf']", namespaces=arxiv_namespaces)
xpath_published = XPath(".//atom:published", namespaces=arxiv_namespaces)
xpath_journal = XPath(".//arxiv:journal_ref", namespaces=arxiv_namespaces)
xpath_category = XPath(".//atom:category/@term", namespaces=arxiv_namespaces)
xpath_comment = XPath("./arxiv:comment", namespaces=arxiv_namespaces)


def request(query: str, params: "OnlineParams") -> None:

    args = {
        "search_query": f"{arxiv_search_prefix}:{query}",
        "start": (params["pageno"] - 1) * arxiv_max_results,
        "max_results": arxiv_max_results,
    }
    params["url"] = f"{base_url}?{urlencode(args)}"


def response(resp: "SXNG_Response") -> EngineResults:

    res = EngineResults()

    dom = etree.fromstring(resp.content)
    for entry in eval_xpath_list(dom, xpath_entry):

        title: str = eval_xpath_getindex(entry, xpath_title, 0).text

        url: str = eval_xpath_getindex(entry, xpath_id, 0).text
        abstract: str = eval_xpath_getindex(entry, xpath_summary, 0).text

        authors: list[str] = [author.text for author in eval_xpath_list(entry, xpath_author_name)]

        #  doi
        doi_element = eval_xpath_getindex(entry, xpath_doi, 0, default=None)
        doi: str = "" if doi_element is None else doi_element.text

        # pdf
        pdf_element = eval_xpath_getindex(entry, xpath_pdf, 0, default=None)
        pdf_url: str = "" if pdf_element is None else pdf_element.attrib.get("href")

        # journal
        journal_element = eval_xpath_getindex(entry, xpath_journal, 0, default=None)
        journal: str = "" if journal_element is None else journal_element.text

        # tags
        tag_elements = eval_xpath(entry, xpath_category)
        tags: list[str] = [str(tag) for tag in tag_elements]

        # comments
        comments_elements = eval_xpath_getindex(entry, xpath_comment, 0, default=None)
        comments: str = "" if comments_elements is None else comments_elements.text

        publishedDate = datetime.strptime(eval_xpath_getindex(entry, xpath_published, 0).text, "%Y-%m-%dT%H:%M:%SZ")

        res.add(
            res.types.Paper(
                url=url,
                title=title,
                publishedDate=publishedDate,
                content=abstract,
                doi=doi,
                authors=authors,
                journal=journal,
                tags=tags,
                comments=comments,
                pdf_url=pdf_url,
            )
        )

    return res
