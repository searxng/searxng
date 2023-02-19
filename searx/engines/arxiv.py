# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 ArXiV (Scientific preprints)
"""

from lxml import etree
from lxml.etree import XPath
from datetime import datetime
from searx.utils import eval_xpath, eval_xpath_list, eval_xpath_getindex

# about
about = {
    "website": 'https://arxiv.org',
    "wikidata_id": 'Q118398',
    "official_api_documentation": 'https://arxiv.org/help/api',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'XML-RSS',
}

categories = ['science', 'scientific publications']
paging = True

base_url = (
    'https://export.arxiv.org/api/query?search_query=all:' + '{query}&start={offset}&max_results={number_of_results}'
)

# engine dependent config
number_of_results = 10

# xpaths
arxiv_namespaces = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}
xpath_entry = XPath('//atom:entry', namespaces=arxiv_namespaces)
xpath_title = XPath('.//atom:title', namespaces=arxiv_namespaces)
xpath_id = XPath('.//atom:id', namespaces=arxiv_namespaces)
xpath_summary = XPath('.//atom:summary', namespaces=arxiv_namespaces)
xpath_author_name = XPath('.//atom:author/atom:name', namespaces=arxiv_namespaces)
xpath_doi = XPath('.//arxiv:doi', namespaces=arxiv_namespaces)
xpath_pdf = XPath('.//atom:link[@title="pdf"]', namespaces=arxiv_namespaces)
xpath_published = XPath('.//atom:published', namespaces=arxiv_namespaces)
xpath_journal = XPath('.//arxiv:journal_ref', namespaces=arxiv_namespaces)
xpath_category = XPath('.//atom:category/@term', namespaces=arxiv_namespaces)
xpath_comment = XPath('./arxiv:comment', namespaces=arxiv_namespaces)


def request(query, params):
    # basic search
    offset = (params['pageno'] - 1) * number_of_results

    string_args = dict(query=query, offset=offset, number_of_results=number_of_results)

    params['url'] = base_url.format(**string_args)

    return params


def response(resp):
    results = []
    dom = etree.fromstring(resp.content)
    for entry in eval_xpath_list(dom, xpath_entry):
        title = eval_xpath_getindex(entry, xpath_title, 0).text

        url = eval_xpath_getindex(entry, xpath_id, 0).text
        abstract = eval_xpath_getindex(entry, xpath_summary, 0).text

        authors = [author.text for author in eval_xpath_list(entry, xpath_author_name)]

        #  doi
        doi_element = eval_xpath_getindex(entry, xpath_doi, 0, default=None)
        doi = None if doi_element is None else doi_element.text

        # pdf
        pdf_element = eval_xpath_getindex(entry, xpath_pdf, 0, default=None)
        pdf_url = None if pdf_element is None else pdf_element.attrib.get('href')

        # journal
        journal_element = eval_xpath_getindex(entry, xpath_journal, 0, default=None)
        journal = None if journal_element is None else journal_element.text

        # tags
        tag_elements = eval_xpath(entry, xpath_category)
        tags = [str(tag) for tag in tag_elements]

        # comments
        comments_elements = eval_xpath_getindex(entry, xpath_comment, 0, default=None)
        comments = None if comments_elements is None else comments_elements.text

        publishedDate = datetime.strptime(eval_xpath_getindex(entry, xpath_published, 0).text, '%Y-%m-%dT%H:%M:%SZ')

        res_dict = {
            'template': 'paper.html',
            'url': url,
            'title': title,
            'publishedDate': publishedDate,
            'content': abstract,
            'doi': doi,
            'authors': authors,
            'journal': journal,
            'tags': tags,
            'comments': comments,
            'pdf_url': pdf_url,
        }

        results.append(res_dict)

    return results
