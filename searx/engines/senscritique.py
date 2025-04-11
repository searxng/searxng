# SPDX-License-Identifier: AGPL-3.0-or-later
"""SensCritique (movies)
"""
from __future__ import annotations

from json import dumps, loads
from typing import Any, Optional
from searx.result_types import EngineResults, MainResult

about = {
    "website": 'https://www.senscritique.com/',
    "wikidata_id": 'Q16676060',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
    'language': 'fr',
}

categories = ['movies']
paging = True
page_size = 16
graphql_url = 'https://apollo.senscritique.com/'

graphql_query = """query SearchProductExplorer($query: String, $offset: Int, $limit: Int,
                    $sortBy: SearchProductExplorerSort) {
  searchProductExplorer(
    query: $query
    filters: []
    sortBy: $sortBy
    offset: $offset
    limit: $limit
  ) {
    items {
      category
      dateRelease
      duration
      id
      originalTitle
      rating
      title
      url
      yearOfProduction
      medias {
        picture
      }
      countries {
        name
      }
      genresInfos {
        label
      }
      directors {
        name
      }
      stats {
        ratingCount
      }
    }
  }
}"""


def request(query: str, params: dict[str, Any]) -> dict[str, Any]:
    offset = (params['pageno'] - 1) * page_size

    data = {
        "operationName": "SearchProductExplorer",
        "variables": {"offset": offset, "limit": page_size, "query": query, "sortBy": "RELEVANCE"},
        "query": graphql_query,
    }

    params['url'] = graphql_url
    params['method'] = 'POST'
    params['headers']['Content-Type'] = 'application/json'
    params['data'] = dumps(data)

    return params


def response(resp) -> EngineResults:
    res = EngineResults()
    response_data = loads(resp.text)

    items = response_data.get('data', {}).get('searchProductExplorer', {}).get('items', [])
    if not items:
        return res

    for item in items:
        result = parse_item(item)
        if not result:
            continue
        res.add(result=result)

    return res


def parse_item(item: dict[str, Any]) -> MainResult | None:
    """Parse a single item from the SensCritique API response"""
    title = item.get('title', '')
    if not title:
        return None
    year = item.get('yearOfProduction')
    original_title = item.get('originalTitle')

    thumbnail: str = ""
    if item.get('medias', {}) and item['medias'].get('picture'):
        thumbnail = item['medias']['picture']

    content_parts = build_content_parts(item, title, original_title)
    url = f"https://www.senscritique.com{item['url']}"

    return MainResult(
        url=url,
        title=title + (f' ({year})' if year else ''),
        content=' | '.join(content_parts),
        thumbnail=thumbnail,
    )


def build_content_parts(item: dict[str, Any], title: str, original_title: Optional[str]) -> list[str]:
    """Build the content parts for an item"""
    content_parts = []

    if item.get('category'):
        content_parts.append(item['category'])

    if original_title and original_title != title:
        content_parts.append(f"Original title: {original_title}")

    if item.get('directors'):
        directors = [director['name'] for director in item['directors']]
        content_parts.append(f"Director(s): {', '.join(directors)}")

    if item.get('countries'):
        countries = [country['name'] for country in item['countries']]
        content_parts.append(f"Country: {', '.join(countries)}")

    if item.get('genresInfos'):
        genres = [genre['label'] for genre in item['genresInfos']]
        content_parts.append(f"Genre(s): {', '.join(genres)}")

    if item.get('duration'):
        minutes = item['duration'] // 60
        if minutes > 0:
            content_parts.append(f"Duration: {minutes} min")

    if item.get('rating') and item.get('stats', {}).get('ratingCount'):
        content_parts.append(f"Rating: {item['rating']}/10 ({item['stats']['ratingCount']} votes)")

    return content_parts
