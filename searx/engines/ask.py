# SPDX-License-Identifier: AGPL-3.0-or-later
"""Ask.com"""

from urllib.parse import urlencode
import dateutil
from lxml import html
from searx import utils

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
max_page = 5

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

    start_tag = 'window.MESON.initialState = {'
    end_tag = '}};'

    dom = html.fromstring(resp.text)
    script = utils.eval_xpath_getindex(dom, '//script', 0, default=None).text

    pos = script.index(start_tag) + len(start_tag) - 1
    script = script[pos:]
    pos = script.index(end_tag) + len(end_tag) - 1
    script = script[:pos]

    json_resp = utils.js_variable_to_python(script)

    results = []

    for item in json_resp['search']['webResults']['results']:

        pubdate_original = item.get('pubdate_original')
        if pubdate_original:
            pubdate_original = dateutil.parser.parse(pubdate_original)
        metadata = [item.get(field) for field in ['category_l1', 'catsy'] if item.get(field)]

        results.append(
            {
                "url": item['url'].split('&ueid')[0],
                "title": item['title'],
                "content": item['abstract'],
                "publishedDate": pubdate_original,
                # "img_src": item.get('image_url') or None, # these are not thumbs / to large
                "metadata": ' | '.join(metadata),
            }
        )

    return results
