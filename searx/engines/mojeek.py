# SPDX-License-Identifier: AGPL-3.0-or-later
"""Mojeek (general, images, news)"""

from datetime import datetime
from urllib.parse import urlencode
from lxml import html

from dateutil.relativedelta import relativedelta
from searx.utils import eval_xpath, eval_xpath_list, extract_text

about = {
    'website': 'https://mojeek.com',
    'wikidata_id': 'Q60747299',
    'official_api_documentation': 'https://www.mojeek.com/support/api/search/request_parameters.html',
    'use_official_api': False,
    'require_api_key': False,
    'results': 'HTML',
}
paging = True  # paging is only supported for general search
safesearch = True
time_range_support = True  # time range search is supported for general and news
max_page = 10

base_url = "https://www.mojeek.com"

categories = ["general", "web"]
search_type = ""  # leave blank for general, other possible values: images, news

results_xpath = '//ul[@class="results-standard"]/li/a[@class="ob"]'
url_xpath = './@href'
title_xpath = '../h2/a'
content_xpath = '..//p[@class="s"]'
suggestion_xpath = '//div[@class="top-info"]/p[@class="top-info spell"]/em/a'

image_results_xpath = '//div[@id="results"]/div[contains(@class, "image")]'
image_url_xpath = './a/@href'
image_title_xpath = './a/@data-title'
image_img_src_xpath = './a/img/@src'

news_results_xpath = '//section[contains(@class, "news-search-result")]//article'
news_url_xpath = './/h2/a/@href'
news_title_xpath = './/h2/a'
news_content_xpath = './/p[@class="s"]'


def init(_):
    if search_type not in ('', 'images', 'news'):
        raise ValueError(f"Invalid search type {search_type}")


def request(query, params):
    args = {
        'q': query,
        'safe': min(params['safesearch'], 1),
        'fmt': search_type,
    }

    if search_type == '':
        args['s'] = 10 * (params['pageno'] - 1)

    if params['time_range'] and search_type != 'images':
        args["since"] = (datetime.now() - relativedelta(**{f"{params['time_range']}s": 1})).strftime("%Y%m%d")
        logger.debug(args["since"])

    params['url'] = f"{base_url}/search?{urlencode(args)}"

    return params


def _general_results(dom):
    results = []

    for result in eval_xpath_list(dom, results_xpath):
        results.append(
            {
                'url': extract_text(eval_xpath(result, url_xpath)),
                'title': extract_text(eval_xpath(result, title_xpath)),
                'content': extract_text(eval_xpath(result, content_xpath)),
            }
        )

    for suggestion in eval_xpath(dom, suggestion_xpath):
        results.append({'suggestion': extract_text(suggestion)})

    return results


def _image_results(dom):
    results = []

    for result in eval_xpath_list(dom, image_results_xpath):
        results.append(
            {
                'template': 'images.html',
                'url': extract_text(eval_xpath(result, image_url_xpath)),
                'title': extract_text(eval_xpath(result, image_title_xpath)),
                'img_src': base_url + extract_text(eval_xpath(result, image_img_src_xpath)),
                'content': '',
            }
        )

    return results


def _news_results(dom):
    results = []

    for result in eval_xpath_list(dom, news_results_xpath):
        results.append(
            {
                'url': extract_text(eval_xpath(result, news_url_xpath)),
                'title': extract_text(eval_xpath(result, news_title_xpath)),
                'content': extract_text(eval_xpath(result, news_content_xpath)),
            }
        )

    return results


def response(resp):
    dom = html.fromstring(resp.text)

    if search_type == '':
        return _general_results(dom)

    if search_type == 'images':
        return _image_results(dom)

    if search_type == 'news':
        return _news_results(dom)

    raise ValueError(f"Invalid search type {search_type}")
