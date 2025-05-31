# SPDX-License-Identifier: AGPL-3.0-or-later
"""CiteSeerX (Computer and Information Science digital library)

"""

from datetime import datetime
from lxml import etree
from lxml.etree import XPath
from searx.utils import eval_xpath, eval_xpath_list, eval_xpath_getindex

# about
about = {
    "website": 'https://citeseerx.ist.psu.edu/',
    "wikidata_id": 'Q259182',  # Wikidata ID for CiteSeerX
    "official_api_documentation": '',  # To be filled if found
    "use_official_api": True,  # Assuming an API exists and will be used
    "require_api_key": False,  # Assuming no API key is needed by default
    "results": 'XML',  # Assuming XML response format, similar to other academic APIs
}

categories = ['science', 'technology', 'computer science', 'scientific publications']
paging = True  # Assuming the API supports pagination

# TODO: Verify base_url and API parameters from actual documentation or testing.
# This is a guess based on common API patterns for search.
# CiteSeerX might use OAI-PMH, which has a different structure, or a custom search API.
# Example: http://citeseerx.ist.psu.edu/search?q={query}&start={offset}&rpp={number_of_results}
# Or an XML API endpoint like: https://citeseerx.ist.psu.edu/api/search?q={query}...
# It's also possible CiteSeerX uses OAI-PMH (Open Archives Initiative Protocol for Metadata Harvesting)
# which would require a different base_url and parsing logic (e.g. verb=ListRecords, metadataPrefix=oai_dc).
# For example: https://citeseerx.ist.psu.edu/oai2?verb=ListRecords&metadataPrefix=oai_dc&set=~{query}
# The current implementation assumes a simpler search API.
base_url = (
    'https://citeseerx.ist.psu.edu/search?q={query}&sort=rlv&start={offset}&rpp={number_of_results}&format=xml'
)
# Parameters like 'sort=rlv' (relevance), 'start' (offset), 'rpp' (results per page) are guesses.
# 'format=xml' is also a guess to request XML response.

number_of_results = 10  # Default number of results per page, adjust as needed.

# xpaths - These are highly speculative and will need adjustment.
# Based on common XML structures for search results and comparison with arxiv.py.
# No specific namespace is assumed for now. If the XML uses namespaces, these XPaths will need to be updated.
xpath_entry = XPath('//result/doc')  # Highly speculative: e.g. <results><doc>...</doc><doc>...</doc></results>
                                    # Or it could be //entry, //item, //record, etc.
xpath_title = XPath('.//title')
xpath_url = XPath('.//url') # This might be a direct link to the paper's landing page on CiteSeerX
xpath_summary = XPath('.//abstract') # Or './/description', './/summary'
xpath_author_name = XPath('.//authors/author') # Assuming a structure like <authors><author>Name</author></authors>
xpath_doi = XPath('.//doi') # Digital Object Identifier
xpath_pdf = XPath('.//download') # Link to the PDF, could be an attribute or text. Often named 'pdf', 'fulltext', 'download'.
xpath_published = XPath('.//year') # Or './/date', './/pubDate'. Date format will also be a guess.
xpath_journal = XPath('.//venue') # Or './/journal', './/publication'
xpath_category = XPath('.//keywords/keyword') # Or './/tags/tag', './/subjects/subject'
xpath_citations = XPath('.//citations') # CiteSeerX is known for citation indexing


def request(query, params):
    offset = (params['pageno'] - 1) * number_of_results

    params['url'] = base_url.format(
        query=query, offset=offset, number_of_results=number_of_results
    )
    return params


def response(resp):
    results = []
    try:
        dom = etree.fromstring(resp.content)
    except etree.XMLSyntaxError:
        # Handle cases where response is not valid XML
        return []

    for entry in eval_xpath_list(dom, xpath_entry):
        title = eval_xpath_getindex(entry, xpath_title, 0, default='').text
        url = eval_xpath_getindex(entry, xpath_url, 0, default='').text
        abstract = eval_xpath_getindex(entry, xpath_summary, 0, default='').text

        authors_elements = eval_xpath_list(entry, xpath_author_name)
        authors = [author.text for author in authors_elements if author.text]

        doi = eval_xpath_getindex(entry, xpath_doi, 0, default='').text

        pdf_element = eval_xpath_getindex(entry, xpath_pdf, 0, default=None)
        pdf_url = None
        if pdf_element is not None:
            # Try to get 'href' attribute first, then text content as fallback
            pdf_url = pdf_element.attrib.get('href', pdf_element.text)

        published_year_str = eval_xpath_getindex(entry, xpath_published, 0, default='').text
        publishedDate = None
        if published_year_str and published_year_str.isdigit():
            try:
                # Assuming only year is available and creating a datetime object for Jan 1st of that year.
                publishedDate = datetime(int(published_year_str), 1, 1)
            except ValueError:
                pass # Should not happen if isdigit() is true and it's a valid year.

        journal = eval_xpath_getindex(entry, xpath_journal, 0, default='').text

        tags_elements = eval_xpath_list(entry, xpath_category)
        tags = [tag.text for tag in tags_elements if tag.text]

        citations_str = eval_xpath_getindex(entry, xpath_citations, 0, default='').text
        citations = None
        if citations_str.isdigit():
            citations = int(citations_str)

        res_dict = {
            'template': 'paper.html', # Assuming similar template to arxiv and europe_pmc
            'url': url,
            'title': title,
            'publishedDate': publishedDate,
            'content': abstract,
            'doi': doi,
            'authors': authors,
            'journal': journal,
            'tags': tags,
            'pdf_url': pdf_url,
            'citations': citations, # Custom field for CiteSeerX
        }
        results.append(res_dict)

    return results
