# SPDX-License-Identifier: AGPL-3.0-or-later
"""Google Gemini AI engine"""

about = {
    "website": 'https://gemini.google.com',
    "wikidata_id": 'Q116221977',
    "official_api_documentation": 'https://ai.google.dev/docs',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['general']
paging = False


def request(query, params):
    """Redirect to Gemini web interface"""

    # Since Gemini requires authentication and scraping is not feasible,
    # return a link to the Gemini interface
    params['url'] = 'https://gemini.google.com'
    return params


def response(resp):
    """Return a link to Gemini"""
    results = []

    results.append({
        'title': f'Ask Gemini about: {resp.search_params.get("query", "")}',
        'url': 'https://gemini.google.com',
        'content': 'Use Google Gemini AI to get answers to your questions. Note: Requires Google account login.',
    })

    return results