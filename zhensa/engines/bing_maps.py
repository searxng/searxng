# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bing Maps"""

from urllib.parse import urlencode

from lxml import html

from zhensa.engines.bing import set_bing_cookies
from zhensa.engines.bing import fetch_traits  # pylint: disable=unused-import
from zhensa.utils import extract_text, eval_xpath_list, eval_xpath_getindex, eval_xpath

about = {
    "website": 'https://www.bing.com/maps',
    "wikidata_id": 'Q186990',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['map']
paging = False

base_url = 'https://www.bing.com/maps'
"""Bing Maps search URL"""


def request(query, params):
    """Assemble a Bing-Maps request."""

    engine_region = traits.get_region(params['zhensa_locale'], traits.all_locale)
    engine_language = traits.get_language(params['zhensa_locale'], 'en')
    set_bing_cookies(params, engine_language, engine_region)

    query_params = {
        'q': query,
    }

    params['url'] = f'{base_url}?{urlencode(query_params)}'

    return params


def response(resp):
    """Get response from Bing-Maps"""
    results = []

    dom = html.fromstring(resp.text)

    # Bing Maps results are in various formats, try to extract location results
    # Look for result containers that might contain map locations
    for result in eval_xpath_list(dom, '//div[contains(@class, "result")] | //li[contains(@class, "result")] | //div[contains(@class, "card")]'):

        # Try to extract title and URL
        title_link = eval_xpath_getindex(result, './/a[contains(@href, "/maps/")]', 0, None)
        if title_link is None:
            continue

        title = extract_text(title_link)
        url = title_link.attrib.get('href')

        if not title or not url:
            continue

        # Extract content/description
        content = extract_text(eval_xpath(result, './/div[contains(@class, "content")] | .//p | .//span'))

        # Extract address information if available
        address_parts = []
        address_selectors = [
            './/span[contains(@class, "address")]',
            './/div[contains(@class, "address")]',
            './/span[contains(text(), ",")]',
        ]

        for selector in address_selectors:
            addr_elements = eval_xpath(result, selector)
            if addr_elements:
                for addr in addr_elements:
                    addr_text = extract_text(addr)
                    if addr_text and addr_text.strip() and len(addr_text.strip()) > 3:
                        address_parts.append(addr_text.strip())

        # Try to extract coordinates from URL if present
        lat, lon = None, None
        import re
        coord_match = re.search(r'cp=([-\d.]+)~([-\d.]+)', url)
        if coord_match:
            lat, lon = coord_match.groups()

        # Build address dict
        address = {'name': title}
        if address_parts:
            # Try to parse address components
            full_address = ' '.join(address_parts)
            address['road'] = full_address

        # Create map result
        map_result = {
            'template': 'map.html',
            'title': title,
            'content': content or '',
            'url': url if url.startswith('http') else f'https://www.bing.com{url}',
            'address': address,
        }

        if lat and lon:
            map_result['latitude'] = lat
            map_result['longitude'] = lon
            map_result['geojson'] = {'type': 'Point', 'coordinates': [float(lon), float(lat)]}

        results.append(map_result)

    # If no specific results found, provide a direct search link
    if not results:
        query = resp.search_params.get('query', '')
        results.append({
            'template': 'map.html',
            'title': f"Search for '{query}' on Bing Maps",
            'url': f"{base_url}?q={query}",
            'address': {
                'name': f"Map search: {query}",
            },
        })

    return results