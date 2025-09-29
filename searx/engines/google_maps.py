# SPDX-License-Identifier: AGPL-3.0-or-later
"""Google Maps"""

import re
from urllib.parse import urlencode, quote_plus

from searx.engines.google import get_google_info, detect_google_sorry

about = {
    "website": 'https://maps.google.com',
    "wikidata_id": 'Q12013',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['map']
paging = False


def request(query, params):
    """Google Maps search request"""

    # Simple Google search URL for maps queries
    query_url = 'https://www.google.com/search?' + urlencode({
        'q': query + ' maps',
        'hl': params.get('language', 'en'),
        'lr': 'lang_' + params.get('language', 'en'),
        'ie': 'utf8',
        'oe': 'utf8',
        'filter': '0',
        'start': 0,
    })

    params['url'] = query_url
    params['headers']['Accept'] = '*/*'
    params['cookies'] = {'CONSENT': 'YES+'}

    return params


def response(resp):
    """Parse Google search results for map-related content"""
    results = []

    detect_google_sorry(resp)

    # Parse the HTML response using the same logic as google.py
    from lxml import html
    from searx.utils import extract_text, eval_xpath_list, eval_xpath, eval_xpath_getindex

    dom = html.fromstring(resp.text)

    # Parse results using the same XPath as google.py
    for result in eval_xpath_list(dom, './/div[contains(@jscontroller, "SC7lYd")]'):
        try:
            title_tag = eval_xpath_getindex(result, './/a/h3[1]', 0, default=None)
            if title_tag is None:
                continue
            title = extract_text(title_tag)

            url = eval_xpath_getindex(result, './/a[h3]/@href', 0, None)
            if url is None:
                continue

            content_nodes = eval_xpath(result, './/div[contains(@data-sncf, "1")]')
            for item in content_nodes:
                for script in item.xpath(".//script"):
                    script.getparent().remove(script)

            content = extract_text(content_nodes)

            if not content:
                continue

            # Check if this is a maps-related result
            is_map_result = (
                'maps.google.com' in url or
                (title and 'maps' in title.lower()) or
                (content and any(keyword in content.lower() for keyword in ['location', 'address', 'directions', 'near', 'place', 'coordinates', 'route', 'navigation']))
            )

            if is_map_result:
                # Extract coordinates if present in URL
                lat, lon = None, None
                coord_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
                if coord_match:
                    lat, lon = coord_match.groups()

                # Transform to map result format
                map_result = {
                    'template': 'map.html',
                    'title': title,
                    'content': content,
                    'url': url,
                    'latitude': lat,
                    'longitude': lon,
                    'address': {
                        'name': title,
                        'road': content.split('·')[0].strip() if '·' in content else content,
                    },
                }

                if lat and lon:
                    map_result['geojson'] = {'type': 'Point', 'coordinates': [float(lon), float(lat)]}

                results.append(map_result)

        except Exception:
            continue

    # If no map results found, provide a direct Google Maps link
    if not results:
        query = resp.search_params.get('query', '').replace(' maps', '')
        results.append({
            'template': 'map.html',
            'title': f"Search for '{query}' on Google Maps",
            'url': f"https://www.google.com/maps/search/{quote_plus(query)}",
            'address': {
                'name': f"Map search: {query}",
            },
        })

    return results