# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Ask.com"""

from urllib.parse import urlencode
import re
from lxml import html

# Metadata
about = {
    "website": "https://www.ask.com/",
    "wikidata_id": 'Q847564',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

# Engine Configuration
categories = ['general']
paging = True

# Base URL
base_url = "https://www.ask.com/web"


def request(query, params):

    query_params = {
        "q": query,
        "page": params["pageno"],
    }

    params["url"] = f"{base_url}?{urlencode(query_params)}"
    return params


def response(resp):

    text = html.fromstring(resp.text).text_content()
    urls_match = re.findall(r'"url":"(.*?)"', text)
    titles_match = re.findall(r'"title":"(.*?)"', text)[3:]
    content_match = re.findall(r'"abstract":"(.*?)"', text)

    results = [
        {
            "url": url,
            "title": title,
            "content": content,
        }
        for url, title, content in zip(urls_match, titles_match, content_match)
        if "&qo=relatedSearchNarrow" not in url
        # Related searches shouldn't be in the search results: www.ask.com/web&q=related
    ]

    return results
