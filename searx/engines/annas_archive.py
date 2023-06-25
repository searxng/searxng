# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Anna's Archive

"""
from typing import List, Dict, Any, Optional
from urllib.parse import quote
from lxml import html

from searx.utils import extract_text, eval_xpath

# about
about: Dict[str, Any] = {
    "website": "https://annas-archive.org/",
    "wikidata_id": "Q115288326",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

# engine dependent config
categories: List[str] = ["files"]
paging: bool = False

# search-url
base_url: str = "https://annas-archive.org"

# xpath queries
xpath_results: str = '//main//a[starts-with(@href,"/md5")]'
xpath_url: str = ".//@href"
xpath_title: str = ".//h3/text()[1]"
xpath_authors: str = './/div[contains(@class, "italic")]'
xpath_publisher: str = './/div[contains(@class, "text-sm")]'
xpath_file_info: str = './/div[contains(@class, "text-xs")]'


def request(query, params: Dict[str, Any]) -> Dict[str, Any]:
    search_url: str = base_url + "/search?q={search_query}&lang={lang}"
    lang: str = ""
    if params["language"] != "all":
        lang = params["language"]

    params["url"] = search_url.format(search_query=quote(query), lang=lang)
    print(params)
    return params


def response(resp) -> List[Dict[str, Optional[str]]]:
    results: List[Dict[str, Optional[str]]] = []
    dom = html.fromstring(resp.text)

    for item in dom.xpath(xpath_results):
        result: Dict[str, Optional[str]] = {}

        result["url"] = base_url + item.xpath(xpath_url)[0]

        result["title"] = extract_text(eval_xpath(item, xpath_title))

        result["content"] = "{publisher}. {authors}. {file_info}".format(
            authors=extract_text(eval_xpath(item, xpath_authors)),
            publisher=extract_text(eval_xpath(item, xpath_publisher)),
            file_info=extract_text(eval_xpath(item, xpath_file_info)),
        )

        results.append(result)

    return results
