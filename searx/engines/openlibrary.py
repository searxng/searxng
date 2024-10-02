# SPDX-License-Identifier: AGPL-3.0-or-later
"""Open library (books)
"""
from urllib.parse import urlencode
import re

from dateutil import parser

about = {
    'website': 'https://openlibrary.org',
    'wikidata_id': 'Q1201876',
    'require_api_key': False,
    'use_official_api': False,
    'official_api_documentation': 'https://openlibrary.org/developers/api',
}

paging = True
categories = []

base_url = "https://openlibrary.org"
results_per_page = 10


def request(query, params):
    args = {
        'q': query,
        'page': params['pageno'],
        'limit': results_per_page,
    }
    params['url'] = f"{base_url}/search.json?{urlencode(args)}"
    return params


def _parse_date(date):
    try:
        return parser.parse(date)
    except parser.ParserError:
        return None


def response(resp):
    results = []

    for item in resp.json().get("docs", []):
        cover = None
        if 'lending_identifier_s' in item:
            cover = f"https://archive.org/services/img/{item['lending_identifier_s']}"

        published = item.get('publish_date')
        if published:
            published_dates = [date for date in map(_parse_date, published) if date]
            if published_dates:
                published = min(published_dates)

        if not published:
            published = parser.parse(str(item.get('first_published_year')))

        result = {
            'template': 'paper.html',
            'url': f"{base_url}{item['key']}",
            'title': item['title'],
            'content': re.sub(r"\{|\}", "", item['first_sentence'][0]) if item.get('first_sentence') else '',
            'isbn': item.get('isbn', [])[:5],
            'authors': item.get('author_name', []),
            'thumbnail': cover,
            'publishedDate': published,
            'tags': item.get('subject', [])[:10] + item.get('place', [])[:10],
        }
        results.append(result)

    return results
