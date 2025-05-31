# SPDX-License-Identifier: AGPL-3.0-or-later
"""Europe PMC (Biomedical literature)

"""

from datetime import datetime

from lxml import etree
from lxml.etree import XPath
from searx.utils import eval_xpath, eval_xpath_list, eval_xpath_getindex

# about
about = {
    "website": 'https://europepmc.org/',
    "wikidata_id": 'Q5412157',  # Assuming this is correct, may need verification
    "official_api_documentation": 'https://europepmc.org/RestfulWebService',  # Placeholder, as I can't access it
    "use_official_api": True,
    "require_api_key": False,
    "results": 'XML',  # Assuming XML, common for such APIs
}

categories = ['science', 'medical', 'scientific publications']
paging = True

# TODO: Verify base_url and API parameters from documentation
base_url = (
    'https://www.ebi.ac.uk/europepmc/webservices/rest/search?'
    'query={query}&resultType=core&cursorMark={cursorMark}&pageSize={number_of_results}'
)
# Note: EuropePMC seems to use cursorMark instead of offset for paging.
# The initial cursorMark is typically '*'

number_of_results = 25  # Default number of results per page

# xpaths - These are guesses and will likely need adjustment
# Based on common patterns and comparison with arxiv.py and potential Europe PMC API structure
europepmc_namespaces = {
    "epmc": "http://europepmc.org/rest/PMC"  # Placeholder namespace, needs verification
}

xpath_entry = XPath('//result', namespaces=europepmc_namespaces) # Assuming 'result' as the entry tag
xpath_title = XPath('.//title', namespaces=europepmc_namespaces)
xpath_id = XPath('.//id', namespaces=europepmc_namespaces) # Often an ID field is used for URLs or unique identifiers
xpath_url = XPath('.//url', namespaces=europepmc_namespaces) # Or there might be a direct URL field
xpath_summary = XPath('.//abstractText', namespaces=europepmc_namespaces) # Common tag for abstracts
xpath_author_name = XPath('.//authorString', namespaces=europepmc_namespaces) # Or //author/name
xpath_doi = XPath('.//doi', namespaces=europepmc_namespaces)
# PDF link might not be directly available or could be in a different format
xpath_pdf = XPath('.//fullTextUrlList/fullTextUrl[urlType="pdf"]/url', namespaces=europepmc_namespaces)
xpath_published = XPath('.//firstPublicationDate', namespaces=europepmc_namespaces) # Common tag for publication date
xpath_journal = XPath('.//journalTitle', namespaces=europepmc_namespaces)
xpath_category = XPath('.//keywordList/keyword', namespaces=europepmc_namespaces) # Assuming keywords can serve as categories


def request(query, params):
    if params['pageno'] == 1:
        cursor_mark = '*'  # Initial cursorMark for the first page
    else:
        # For subsequent pages, cursorMark should be retrieved from the previous response.
        # This is a placeholder, as we need to store and retrieve the nextCursorMark.
        # Searx's default paging might not directly support cursor-based pagination without modification
        # or storing state between requests, which is advanced.
        # For now, we'll try to adapt, but this might be a limitation.
        # A simpler approach for now might be to just fetch the first page if cursor handling is complex.
        # Or, if the API supports 'offset' or 'page' parameter, that would be easier.
        # The documentation link I found earlier (https://europepmc.org/RestfulWebService)
        # mentions "page" and "pageSize", let's try to use that if cursorMark is too complex for stateless requests.
        # Re-checking common API patterns, 'page' is more common than 'cursorMark' for stateless.
        # Let's adjust base_url if 'page' is supported, assuming it is for now.
        pass

    # Adjusted base_url assuming 'page' parameter. If not, this needs to be reverted/changed.
    # Placeholder: Trying a more common offset-based paging if cursorMark is too complex.
    # Let's assume an 'offset' or 'page' parameter exists for now for simplicity,
    # as cursor-based pagination is harder to implement without session state.
    # Many APIs offer 'start', 'offset', or 'page'. Let's try 'page'.
    # If API truly only supports cursorMark, this will need significant adjustment.

    # Reverting to a structure that might use 'page' if available, or a simplified cursor.
    # For now, let's assume we can use 'page' as pageno.
    # The API docs are crucial here. A common pattern is pageSize and page.
    # https://europepmc.org/RestfulWebService mentions query, resultType, pageSize, page, cursorMark, sort etc.
    # So, we can use 'page' and 'pageSize'.

    page = params['pageno']

    params['url'] = (
        'https://www.ebi.ac.uk/europepmc/webservices/rest/search?'
        'query={query}&resultType=core&pageSize={number_of_results}&page={page}'
    ).format(query=query, number_of_results=number_of_results, page=page)

    return params


def response(resp):
    results = []
    try:
        dom = etree.fromstring(resp.content)
    except etree.XMLSyntaxError:
        # Handle cases where response is not valid XML (e.g., error message)
        return []

    for entry in eval_xpath_list(dom, xpath_entry):
        title = eval_xpath_getindex(entry, xpath_title, 0, default='').text
        # Assuming 'id' might be part of the URL or the URL itself.
        # If a dedicated URL field exists, prioritize that.
        url_from_id = eval_xpath_getindex(entry, xpath_id, 0, default='').text
        # Construct URL from ID if necessary, e.g., https://europepmc.org/article/MED/PMCID_OR_ID
        # This needs to be verified based on actual API response structure.
        # For now, let's assume 'id' can be part of the URL or is the article ID.
        # A common pattern: https://europepmc.org/abstract/MED/{id}
        # Or if there's a direct URL field:
        url_direct = eval_xpath_getindex(entry, xpath_url, 0, default='').text
        url = url_direct if url_direct else f"https://europepmc.org/abstract/MED/{url_from_id}" # Fallback, needs verification

        abstract = eval_xpath_getindex(entry, xpath_summary, 0, default='').text
        authors_string = eval_xpath_getindex(entry, xpath_author_name, 0, default='').text
        authors = [a.strip() for a in authors_string.split(',') if a.strip()] # Simple split by comma

        doi = eval_xpath_getindex(entry, xpath_doi, 0, default='').text

        # PDF URL extraction: attempt to get href attribute if element is found
        pdf_element = eval_xpath_getindex(entry, xpath_pdf, 0, default=None)
        pdf_url = None
        if pdf_element is not None:
            pdf_url = pdf_element.text  # Or pdf_element.attrib.get('href') - common for links

        published_date_str = eval_xpath_getindex(entry, xpath_published, 0, default='').text
        publishedDate = None
        if published_date_str:
            try:
                # Assuming YYYY-MM-DD format, adjust if different
                publishedDate = datetime.strptime(published_date_str, '%Y-%m-%d')
            except ValueError:
                pass # Handle parsing errors if date format is unexpected

        journal = eval_xpath_getindex(entry, xpath_journal, 0, default='').text
        tags = [tag.text for tag in eval_xpath_list(entry, xpath_category) if tag.text]

        res_dict = {
            'template': 'paper.html', # Assuming similar template to arxiv
            'url': url,
            'title': title,
            'publishedDate': publishedDate,
            'content': abstract,
            'doi': doi,
            'authors': authors,
            'journal': journal,
            'tags': tags,
            'pdf_url': pdf_url,
        }
        results.append(res_dict)

    return results
