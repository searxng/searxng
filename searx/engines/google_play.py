# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Google Play Apps & Google Play Movies
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

send_accept_language_header = True

play_categ = None  # apps|movies
base_url = 'https://play.google.com'
search_url = base_url + "/store/search?{query}&c={play_categ}"


def request(query, params):

    if play_categ not in ('movies', 'apps'):
        raise ValueError(f"unknown google play category: {play_categ}")

    params["url"] = search_url.format(
        query=urlencode({"q": query}),
        play_categ=play_categ,
    )
    params['cookies']['CONSENT'] = "YES+"

    return params


def response(resp):

    if play_categ == 'movies':
        return response_movies(resp)
    if play_categ == 'apps':
        return response_apps(resp)
    return []


def response_movies(resp):

    results = []
    dom = html.fromstring(resp.text)

    for section in eval_xpath(dom, '//c-wiz/section/header/..'):
        sec_name = extract_text(eval_xpath(section, './header'))
        for item in eval_xpath(section, './/a'):
            url = base_url + item.get('href')
            div_1, div_2 = eval_xpath(item, './div')[:2]
            title = extract_text(eval_xpath(div_2, './div[@title]'))
            metadata = extract_text(eval_xpath(div_2, './div[@class]'))
            img = eval_xpath(div_1, './/img')[0]
            img_src = img.get('src')
            results.append(
                {
                    "url": url,
                    "title": title,
                    "content": sec_name,
                    "img_src": img_src,
                    'metadata': metadata,
                    'template': 'videos.html',
                }
            )
    return results


def response_apps(resp):

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
