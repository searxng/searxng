# SPDX-License-Identifier: AGPL-3.0-or-later
"""UXwing (images)"""

from urllib.parse import quote_plus
from lxml import html

from searx.utils import eval_xpath, eval_xpath_list, extract_text

about = {
    "website": 'https://uxwing.com',
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}
categories = ['images', 'icons']

base_url = "https://uxwing.com"
enable_http2 = False


def request(query, params):
    params['url'] = f"{base_url}/?s={quote_plus(query)}"
    return params


def response(resp):
    results = []

    doc = html.fromstring(resp.text)
    for result in eval_xpath_list(doc, "//article[starts-with(@id, 'post')]"):
        classes = extract_text(eval_xpath(result, "./@class")).split(" ")
        tags = []
        for css_class in classes:
            for prefix in ("category", "tag"):
                if css_class.startswith(prefix):
                    tag = css_class.removeprefix(prefix)
                    tags.append(tag.replace("-", " ").title())

        results.append(
            {
                'template': 'images.html',
                'url': extract_text(eval_xpath(result, "./a/@href")),
                'img_src': extract_text(eval_xpath(result, ".//img/@src")),
                'title': extract_text(eval_xpath(result, ".//img/@alt")),
                'content': ', '.join(tags),
            }
        )

    return results
