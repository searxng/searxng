# SPDX-License-Identifier: AGPL-3.0-or-later
"""
  Google Play Apps
"""

from urllib.parse import urlencode
from lxml import html
from searx.utils import (
    eval_xpath,
    extract_url,
    extract_text,
    eval_xpath_list,
    eval_xpath_getindex,
)

about = {
    "website": "https://play.google.com/",
    "wikidata_id": "Q79576",
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

categories = ["files", "apps"]
search_url = "https://play.google.com/store/search?{query}&c=apps"


def request(query, params):
    params["url"] = search_url.format(query=urlencode({"q": query}))

    return params


def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    if eval_xpath(dom, '//div[@class="v6DsQb"]'):
        return []

    spot = eval_xpath_getindex(dom, '//div[@class="ipRz4"]', 0, None)
    if spot is not None:
        url = extract_url(eval_xpath(spot, './a[@class="Qfxief"]/@href'), search_url)
        title = extract_text(eval_xpath(spot, './/div[@class="vWM94c"]'))
        content = extract_text(eval_xpath(spot, './/div[@class="LbQbAe"]'))
        img = extract_text(eval_xpath(spot, './/img[@class="T75of bzqKMd"]/@src'))

        results.append({"url": url, "title": title, "content": content, "img_src": img})

    more = eval_xpath_list(dom, '//c-wiz[@jsrenderer="RBsfwb"]//div[@role="listitem"]', min_len=1)
    for result in more:
        url = extract_url(eval_xpath(result, ".//a/@href"), search_url)
        title = extract_text(eval_xpath(result, './/span[@class="DdYX5"]'))
        content = extract_text(eval_xpath(result, './/span[@class="wMUdtb"]'))
        img = extract_text(
            eval_xpath(
                result,
                './/img[@class="T75of stzEZd" or @class="T75of etjhNc Q8CSx "]/@src',
            )
        )

        results.append({"url": url, "title": title, "content": content, "img_src": img})

    for suggestion in eval_xpath_list(dom, '//c-wiz[@jsrenderer="qyd4Kb"]//div[@class="ULeU3b neq64b"]'):
        results.append({"suggestion": extract_text(eval_xpath(suggestion, './/div[@class="Epkrse "]'))})

    return results
