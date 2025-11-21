# SPDX-License-Identifier: AGPL-3.0-or-later
"""PubMed_ comprises more than 39 million citations for biomedical literature
from MEDLINE, life science journals, and online books. Citations may include
links to full text content from PubMed Central and publisher web sites.

.. _PubMed: https://pubmed.ncbi.nlm.nih.gov/

Configuration
=============

.. code:: yaml

   - name: pubmed
     engine: pubmed
     shortcut: pub

Implementations
===============

"""

import typing as t

from datetime import datetime
from urllib.parse import urlencode

from lxml import etree

from searx.result_types import EngineResults
from searx.network import get
from searx.utils import (
    eval_xpath_getindex,
    eval_xpath_list,
    extract_text,
    ElementType,
)

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://www.ncbi.nlm.nih.gov/pubmed/",
    "wikidata_id": "Q1540899",
    "official_api_documentation": {
        "url": "https://www.ncbi.nlm.nih.gov/home/develop/api/",
        "comment": "More info on api: https://www.ncbi.nlm.nih.gov/books/NBK25501/",
    },
    "use_official_api": True,
    "require_api_key": False,
    "results": "XML",
}

categories = ["science", "scientific publications"]

eutils_api = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# engine dependent config
number_of_results = 10
pubmed_url = "https://www.ncbi.nlm.nih.gov/pubmed/"


def request(query: str, params: "OnlineParams") -> None:

    args = urlencode(
        {
            "db": "pubmed",
            "term": query,
            "retstart": (params["pageno"] - 1) * number_of_results,
            "hits": number_of_results,
        }
    )
    esearch_url = f"{eutils_api}/esearch.fcgi?{args}"
    # DTD: https://eutils.ncbi.nlm.nih.gov/eutils/dtd/20060628/esearch.dtd
    esearch_resp: "SXNG_Response" = get(esearch_url, timeout=3)
    pmids_results = etree.XML(esearch_resp.content)
    pmids: list[str] = [i.text for i in pmids_results.xpath("//eSearchResult/IdList/Id")]

    # send efetch request with the IDs from esearch response
    args = urlencode(
        {
            "db": "pubmed",
            "retmode": "xml",
            "id": ",".join(pmids),
        }
    )
    efetch_url = f"{eutils_api}/efetch.fcgi?{args}"
    params["url"] = efetch_url


def response(resp: "SXNG_Response") -> EngineResults:  # pylint: disable=too-many-locals

    # DTD: https://dtd.nlm.nih.gov/ncbi/pubmed/out/pubmed_250101.dtd

    # parse efetch response
    efetch_xml = etree.XML(resp.content)
    res = EngineResults()

    def _field_txt(xml: ElementType, xpath_str: str) -> str:
        elem = eval_xpath_getindex(xml, xpath_str, 0, default="")
        return extract_text(elem, allow_none=True) or ""

    for pubmed_article in eval_xpath_list(efetch_xml, "//PubmedArticle"):

        medline_citation: ElementType = eval_xpath_getindex(pubmed_article, "./MedlineCitation", 0)
        pubmed_data: ElementType = eval_xpath_getindex(pubmed_article, "./PubmedData", 0)

        title: str = eval_xpath_getindex(medline_citation, ".//Article/ArticleTitle", 0).text
        pmid: str = eval_xpath_getindex(medline_citation, ".//PMID", 0).text
        url: str = pubmed_url + pmid
        content = _field_txt(medline_citation, ".//Abstract/AbstractText//text()")
        doi = _field_txt(medline_citation, ".//ELocationID[@EIdType='doi']/text()")
        journal = _field_txt(medline_citation, "./Article/Journal/Title/text()")
        issn = _field_txt(medline_citation, "./Article/Journal/ISSN/text()")

        authors: list[str] = []

        for author in eval_xpath_list(medline_citation, "./Article/AuthorList/Author"):
            f = eval_xpath_getindex(author, "./ForeName", 0, default=None)
            l = eval_xpath_getindex(author, "./LastName", 0, default=None)
            author_name = f"{f.text if f is not None else ''} {l.text if l is not None else ''}".strip()
            if author_name:
                authors.append(author_name)

        accepted_date = eval_xpath_getindex(
            pubmed_data, "./History//PubMedPubDate[@PubStatus='accepted']", 0, default=None
        )
        pub_date = None
        if accepted_date is not None:
            year = eval_xpath_getindex(accepted_date, "./Year", 0)
            month = eval_xpath_getindex(accepted_date, "./Month", 0)
            day = eval_xpath_getindex(accepted_date, "./Day", 0)
            try:
                pub_date = datetime(year=int(year.text), month=int(month.text), day=int(day.text))
            except ValueError:
                pass

        res.add(
            res.types.Paper(
                url=url,
                title=title,
                content=content,
                journal=journal,
                issn=[issn],
                authors=authors,
                doi=doi,
                publishedDate=pub_date,
            )
        )
    return res
