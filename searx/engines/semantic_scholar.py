# SPDX-License-Identifier: AGPL-3.0-or-later
"""Semantic Scholar (Scientific articles)

API documentation: https://api.semanticscholar.org/api-docs/graph (though direct access to details was problematic)
Key details:
- Endpoint: /graph/v1/paper/search
- Response: JSON
- Pagination: offset, limit
- Fields: title, abstract, authors, venue, year, paperId, externalIds (DOI), openAccessPdf, url
"""

import json
from datetime import datetime
from searx.utils import get_json_result, get_json_list_value, get_json_string_value, get_json_int_value

# about
about = {
    "website": 'https://www.semanticscholar.org/',
    "wikidata_id": 'Q22680419', # Wikidata ID for Semantic Scholar
    "official_api_documentation": 'https://api.semanticscholar.org/api-docs/graph',
    "use_official_api": True,
    "require_api_key": False, # API key recommended for higher rate limits, but not strictly required
    "results": 'JSON',
    "categories": ['science', 'technology', 'computer science', 'medical', 'scientific publications'],
    "attributes": {  # For informing users about potential API key benefits
        "api_key": "recommended for higher rate limits (1 request/second vs 1000 requests/5 minutes shared for anonymous users)"
    }
}

paging = True
number_of_results = 10  # Default limit, can be up to 100 according to general API practices.
                        # The API docs state "limit: Up to 100 results to return in each request. Defaults to 100."
                        # Let's use a higher default, e.g., 20 or 50, if appropriate for Searx.
                        # Sticking to 10 for now as it's common in other engines.

# Base URL for the paper search API
base_url = 'https://api.semanticscholar.org/graph/v1/paper/search'

# Fields to request from the API
# Ref: https://api.semanticscholar.org/api-docs/graph#tag/Paper-Data/operation/get_graph_v1_paper_search
# Common fields: paperId, externalIds, url, title, abstract, venue, year, authors, openAccessPdf
fields_to_request = [
    'paperId',
    'externalIds', # Contains DOI
    'url',         # URL to Semantic Scholar page
    'title',
    'abstract',
    'venue',
    'year',
    'authors',     # Array of authors: {authorId, name}
    'openAccessPdf' # Object: {url, status}
]
fields_param = ','.join(fields_to_request)

def request(query, params):
    offset = (params['pageno'] - 1) * number_of_results
    # According to docs, query parameter for GET is 'query'.
    # For POST, it's a JSON body: { "query": "string", "facets": ..., ... }
    # We are using GET.
    api_url = f"{base_url}?query={query}&offset={offset}&limit={number_of_results}&fields={fields_param}"

    params['url'] = api_url
    # Searx typically handles URL encoding for query parameters.
    return params

def response(resp):
    results = []
    search_data = resp.json()

    # Expected structure:
    # {
    #   "total": int,
    #   "offset": int,
    #   "next": int (next offset, if more results),
    #   "data": [ {paper}, {paper}, ... ]
    # }

    # Pass total number of results to searx if pageno is 1
    # This helps searx display the total number of results found
    if params['pageno'] == 1:
        total = get_json_int_value(search_data, 'total', 0)
        if total > 0:
            results.append({'number_of_results': total})

    papers = get_json_list_value(search_data, 'data', [])

    for paper in papers:
        title = get_json_string_value(paper, 'title', '')
        paper_id = get_json_string_value(paper, 'paperId', '')

        # URL to the paper on Semantic Scholar website
        # The 'url' field from API is usually the correct one.
        url = get_json_string_value(paper, 'url', '')
        if not url and paper_id: # Fallback if 'url' is missing
            url = f"https://www.semanticscholar.org/paper/{paper_id}"

        abstract = get_json_string_value(paper, 'abstract', '')
        venue = get_json_string_value(paper, 'venue', '')
        year_val = get_json_result(paper, 'year') # Can be int or string

        publishedDate = None
        if year_val is not None:
            try:
                year_int = int(str(year_val)) # Ensure it's an int
                publishedDate = datetime(year_int, 1, 1)
            except ValueError:
                pass # If year format is unexpected

        authors_list = get_json_list_value(paper, 'authors', [])
        # Each author in authors_list is expected to be like: {"authorId": "...", "name": "..."}
        authors = [get_json_string_value(author, 'name', '') for author in authors_list if get_json_string_value(author, 'name')]

        external_ids = get_json_result(paper, 'externalIds', {}) # This is a dict e.g. {"DOI": "..."}
        doi = get_json_string_value(external_ids, 'DOI', '') if external_ids else ''

        open_access_pdf_info = get_json_result(paper, 'openAccessPdf', {}) # This is a dict e.g. {"url": "...", "status": "..."}
        pdf_url = get_json_string_value(open_access_pdf_info, 'url', '') if open_access_pdf_info else ''

        content = abstract if abstract else ''

        res_dict = {
            'template': 'paper.html',
            'url': url,
            'title': title,
            'publishedDate': publishedDate,
            'content': content,
            'doi': doi,
            'authors': authors,
            'venue': venue,
            'pdf_url': pdf_url,
            'paper_id': paper_id
        }
        results.append(res_dict)

    return results
