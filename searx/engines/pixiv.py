import httpx
from urllib.parse import urlencode
from datetime import datetime

# Engine metadata
about = {
    "website": "https://www.pixiv.net/",
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

# Engine configuration
paging = True
categories = ['images']

# Search URL
base_url = "https://www.pixiv.net/ajax/search/illustrations"


def request(query, params):
    page_number = params.get("pageno", 1)
    query_params = {
        "word": query,
        "order": "date_d",
        "mode": "all",
        "p": page_number,
        "s_mode": "s_tag_full",
        "type": "illust_and_ugoira",
        "lang": "en",
    }

    with httpx.Client() as client:
        response = client.get(f"{base_url}/{query}?{urlencode(query_params)}")
        params["url"] = response.url

    return params


def format_results(item):
    title = item["title"]
    url = item["url"]
    user_id = item["userId"]
    user_name = item["userName"]
    image_url = item["url"]


    return {
        "title": title,
        "url": image_url,
        "author": f"{user_name} (ID: {user_id})",
        "img_src": image_url,
        "source": 'pixiv.net',
        "template": "images.html",
    }


def response(resp):
    data = resp.json()
    illustrations = data["body"]["illust"]["data"]
    results = [format_results(item) for item in illustrations]

    return results