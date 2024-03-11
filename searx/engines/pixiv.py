# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pixiv (images)"""

from urllib.parse import urlencode
import random

# Engine metadata
about = {
    "website": 'https://www.pixiv.net/',
    "wikidata_id": 'Q306956',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

# Engine configuration
paging = True
categories = ['images']

# Search URL
base_url = "https://www.pixiv.net/ajax/search/illustrations"
pixiv_image_proxies: list = []


def request(query, params):
    query_params = {
        "word": query,
        "order": "date_d",
        "mode": "all",
        "p": params["pageno"],
        "s_mode": "s_tag_full",
        "type": "illust_and_ugoira",
        "lang": "en",
    }

    params["url"] = f"{base_url}/{query}?{urlencode(query_params)}"

    return params


def response(resp):
    results = []
    data = resp.json()

    for item in data["body"]["illust"]["data"]:

        image_url = item["url"]
        pixiv_proxy = random.choice(pixiv_image_proxies)
        proxy_image_url = image_url.replace("https://i.pximg.net", pixiv_proxy)
        proxy_full_image_url = (
            proxy_image_url.replace("/c/250x250_80_a2/", "/")
            .replace("_square1200.jpg", "_master1200.jpg")
            .replace("custom-thumb", "img-master")
            .replace("_custom1200.jpg", "_master1200.jpg")
        )

        results.append(
            {
                "title": item.get("title"),
                "url": proxy_full_image_url,
                'content': item.get('alt'),
                "author": f"{item.get('userName')} (ID: {item.get('userId')})",
                "img_src": proxy_full_image_url,
                "thumbnail_src": proxy_image_url,
                "source": 'pixiv.net',
                "template": "images.html",
            }
        )

    return results
