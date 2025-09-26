# SPDX-License-Identifier: AGPL-3.0-or-later
"""Chefkoch is a German database of recipes."""

from datetime import datetime
from urllib.parse import urlencode

about = {
    'website': "https://www.chefkoch.de",
    'official_api_documentation': None,
    'use_official_api': False,
    'require_api_key': False,
    'results': 'JSON',
    'language': 'de',
}

paging = True
categories = []

number_of_results = 20
skip_premium = True


base_url = "https://api.chefkoch.de"
thumbnail_format = "crop-240x300"


def request(query, params):
    args = {'query': query, 'limit': number_of_results, 'offset': (params['pageno'] - 1) * number_of_results}
    params['url'] = f"{base_url}/v2/search-gateway/recipes?{urlencode(args)}"
    return params


def response(resp):
    results = []

    json = resp.json()

    for result in json['results']:
        recipe = result['recipe']

        if skip_premium and (recipe['isPremium'] or recipe['isPlus']):
            continue

        publishedDate = None
        if recipe['submissionDate']:
            publishedDate = datetime.strptime(result['recipe']['submissionDate'][:19], "%Y-%m-%dT%H:%M:%S")

        content = [
            f"Schwierigkeitsstufe (1-3): {recipe['difficulty']}",
            f"Zubereitungszeit: {recipe['preparationTime']}min",
            f"Anzahl der Zutaten: {recipe['ingredientCount']}",
        ]

        if recipe['subtitle']:
            content.insert(0, recipe['subtitle'])

        results.append(
            {
                'url': recipe['siteUrl'],
                'title': recipe['title'],
                'content': " | ".join(content),
                'thumbnail': recipe['previewImageUrlTemplate'].replace("<format>", thumbnail_format),
                'publishedDate': publishedDate,
            }
        )

    return results
