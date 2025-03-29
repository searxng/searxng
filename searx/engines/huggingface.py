# SPDX-License-Identifier: AGPL-3.0-or-later
"""Hugging Face search engine for searxng"""

from urllib.parse import urlencode
from datetime import datetime

from searx.exceptions import SearxEngineAPIException
from searx.utils import html_to_text

about = {
    "website": "https://huggingface.co/",
    "wikidata_id": "Q108943604",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

categories = ['it', 'repos']

base_url = "https://huggingface.co"

huggingface_endpoint = 'models'
"""Hugging Face supports datasets, models, spaces as search endpoint.

- ``datasets``: search for datasets
- ``models``: search for models
- ``spaces``: search for spaces
"""


def init(_):
    if huggingface_endpoint not in ('datasets', 'models', 'spaces'):
        raise SearxEngineAPIException(f"Unsupported Hugging Face endpoint: {huggingface_endpoint}")


def request(query, params):
    query_params = {
        "direction": -1,
        "search": query,
    }

    params["url"] = f"{base_url}/api/{huggingface_endpoint}?{urlencode(query_params)}"

    return params


def response(resp):
    results = []

    data = resp.json()

    for entry in data:
        if huggingface_endpoint != 'models':
            url = f"{base_url}/{huggingface_endpoint}/{entry['id']}"
        else:
            url = f"{base_url}/{entry['id']}"

        published_date = None
        try:
            published_date = datetime.strptime(entry["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ")
        except (ValueError, TypeError):
            pass

        contents = []
        if entry.get("likes"):
            contents.append(f"Likes: {entry['likes']}")
        if entry.get("downloads"):
            contents.append(f"Downloads: {entry['downloads']:,}")
        if entry.get("tags"):
            contents.append(f"Tags: {', '.join(entry['tags'])}")
        if entry.get("description"):
            contents.append(f"Description: {entry['description']}")

        results.append(
            {
                'title': entry["id"],
                'url': url,
                'content': html_to_text(" | ".join(contents)),
                'publishedDate': published_date,
            }
        )

    return results
