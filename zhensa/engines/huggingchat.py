# SPDX-License-Identifier: AGPL-3.0-or-later
"""Hugging Face Chat AI engine"""

about = {
    "website": 'https://huggingface.co/chat',
    "wikidata_id": 'Q115120725',
    "official_api_documentation": 'https://huggingface.co/docs',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['general']
paging = False


def request(query, params):
    """Redirect to Hugging Chat web interface"""

    params['url'] = 'https://huggingface.co/chat'
    return params


def response(resp):
    """Return a link to Hugging Chat"""
    results = []

    results.append({
        'title': f'Ask Hugging Chat about: {resp.search_params.get("query", "")}',
        'url': 'https://huggingface.co/chat',
        'content': 'Use Hugging Face Chat AI to get answers to your questions. Free and open source AI models.',
    })

    return results