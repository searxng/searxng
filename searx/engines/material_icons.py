# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Material Icons (images)
"""

import re
from json import loads

about = {
    "website": 'https://fonts.google.com/icons',
    "wikidata_id": 'Q107315222',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}
search_url = "https://fonts.google.com/metadata/icons?key=material_symbols&incomplete=true"
result_url = "https://fonts.google.com/icons?icon.query={query}&selected=Material+Symbols+Outlined:{icon_name}:FILL@0{fill};wght@400;GRAD@0;opsz@24"  # pylint: disable=line-too-long
img_src_url = "https://fonts.gstatic.com/s/i/short-term/release/materialsymbolsoutlined/{icon_name}/{svg_type}/24px.svg"
filled_regex = r"(fill)(ed)?"


def request(query, params):
    params['url'] = search_url
    params['query'] = query
    return params


def response(resp):
    results = []

    query = resp.search_params["query"].lower()
    json_results = loads(resp.text[5:])

    outlined = not re.findall(filled_regex, query)
    query = re.sub(filled_regex, "", query).strip()
    svg_type = "fill1" if not outlined else "default"

    query_parts = query.split(" ")

    for result in json_results["icons"]:
        for part in query_parts:
            if part in result["name"] or part in result["tags"] or part in result["categories"]:
                break
        else:
            continue

        tags = [tag.title() for tag in result["tags"]]
        categories = [category.title() for category in result["categories"]]

        results.append(
            {
                'template': 'images.html',
                'url': result_url.format(icon_name=result["name"], query=result["name"], fill=0 if outlined else 1),
                'img_src': img_src_url.format(icon_name=result["name"], svg_type=svg_type),
                'title': result["name"].replace("_", "").title(),
                'content': ", ".join(tags) + " / " + ", ".join(categories),
            }
        )

    return results
