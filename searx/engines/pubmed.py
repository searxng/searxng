# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 PubMed (Scholar publications)
"""

from lxml import etree
from datetime import datetime
from urllib.parse import urlencode
from searx.network import get
from searx.utils import (
    eval_xpath_getindex,
    eval_xpath_list,
    extract_text,
)

# about
about = {
    "website": 'https://www.ncbi.nlm.nih.gov/pubmed/',
    "wikidata_id": 'Q1540899',
    "official_api_documentation": {
        'url': 'https://www.ncbi.nlm.nih.gov/home/develop/api/',
        'comment': 'More info on api: https://www.ncbi.nlm.nih.gov/books/NBK25501/',
    },
    "use_official_api": True,
    "require_api_key": False,
    "results": 'XML',
}

categories = ['science', 'scientific publications']

base_url = (
    'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi' + '?db=pubmed&{query}&retstart={offset}&retmax={hits}'
)

# engine dependent config
number_of_results = 10
pubmed_url = 'https://www.ncbi.nlm.nih.gov/pubmed/'


def request(query, params):
    # basic search
    offset = (params['pageno'] - 1) * number_of_results

    string_args = dict(query=urlencode({'term': query}), offset=offset, hits=number_of_results)

    params['url'] = base_url.format(**string_args)

    return params


def response(resp):
    results = []

    # First retrieve notice of each result
    pubmed_retrieve_api_url = (
        'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?' + 'db=pubmed&retmode=xml&id={pmids_string}'
    )

    pmids_results = etree.XML(resp.content)
    pmids = pmids_results.xpath('//eSearchResult/IdList/Id')
    pmids_string = ''

    for item in pmids:
        pmids_string += item.text + ','

    retrieve_notice_args = dict(pmids_string=pmids_string)

    retrieve_url_encoded = pubmed_retrieve_api_url.format(**retrieve_notice_args)

    search_results_response = get(retrieve_url_encoded).content
    search_results = etree.XML(search_results_response)
    for entry in eval_xpath_list(search_results, '//PubmedArticle'):
        medline = eval_xpath_getindex(entry, './MedlineCitation', 0)

        title = eval_xpath_getindex(medline, './/Article/ArticleTitle', 0).text
        pmid = eval_xpath_getindex(medline, './/PMID', 0).text
        url = pubmed_url + pmid
        content = extract_text(
            eval_xpath_getindex(medline, './/Abstract/AbstractText//text()', 0, default=None), allow_none=True
        )
        doi = extract_text(
            eval_xpath_getindex(medline, './/ELocationID[@EIdType="doi"]/text()', 0, default=None), allow_none=True
        )
        journal = extract_text(
            eval_xpath_getindex(medline, './Article/Journal/Title/text()', 0, default=None), allow_none=True
        )
        issn = extract_text(
            eval_xpath_getindex(medline, './Article/Journal/ISSN/text()', 0, default=None), allow_none=True
        )
        authors = []
        for author in eval_xpath_list(medline, './Article/AuthorList/Author'):
            f = eval_xpath_getindex(author, './ForeName', 0, default=None)
            l = eval_xpath_getindex(author, './LastName', 0, default=None)
            f = '' if f is None else f.text
            l = '' if l is None else l.text
            authors.append((f + ' ' + l).strip())

        res_dict = {
            'template': 'paper.html',
            'url': url,
            'title': title,
            'content': content,
            'journal': journal,
            'issn': [issn],
            'authors': authors,
            'doi': doi,
        }

        accepted_date = eval_xpath_getindex(
            entry, './PubmedData/History//PubMedPubDate[@PubStatus="accepted"]', 0, default=None
        )
        if accepted_date is not None:
            year = eval_xpath_getindex(accepted_date, './Year', 0)
            month = eval_xpath_getindex(accepted_date, './Month', 0)
            day = eval_xpath_getindex(accepted_date, './Day', 0)
            try:
                publishedDate = datetime.strptime(
                    year.text + '-' + month.text + '-' + day.text,
                    '%Y-%m-%d',
                )
                res_dict['publishedDate'] = publishedDate
            except Exception as e:
                print(e)

        results.append(res_dict)

    return results
