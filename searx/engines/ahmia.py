# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Ahmia (Onions)
"""

import typing as t

from urllib.parse import urlencode, urlparse, parse_qs
from lxml.html import fromstring
from searx.utils import gen_useragent, ElementType
from searx.engines.xpath import extract_url, extract_text, eval_xpath_list, eval_xpath
from searx.network import get
from searx.enginelib import EngineCache

# about
about = {
    "website": 'http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion',
    "wikidata_id": 'Q18693938',
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine config
categories = ['onions']
paging = True
page_size = 10

# search url
base_url = 'http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion'
search_url = 'http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/search/?{query}'
time_range_support = True
time_range_dict = {'day': 1, 'week': 7, 'month': 30}

# xpaths
results_xpath = '//li[@class="result"]'
url_xpath = './h4/a/@href'
title_xpath = './h4/a[1]'
content_xpath = './/p[1]'
correction_xpath = '//*[@id="didYouMean"]//a'
number_of_results_xpath = '//*[@id="totalResults"]'
name_token_xpath = '//form[@id="searchForm"]/input[@type="hidden"]/@name'
value_token_xpath = '//form[@id="searchForm"]/input[@type="hidden"]/@value'

CACHE: EngineCache
"""Persistent (SQLite) key/value cache that deletes its values after ``expire``
seconds."""


def setup(engine_settings: dict[str, t.Any]) -> bool:
    global CACHE  # pylint: disable=global-statement
    CACHE = EngineCache(engine_settings["name"])
    return True


def _get_tokens(dom: ElementType | None = None) -> str:
    """
    The tokens are hidden in a hidden input field.
    They update every minute, but allow up to 1 hour old tokens to be used.
    To spend the least amount of requests, it is best to always get the newest
    tokens from each request. In worst case if it has expired, it would
    need to do a total of 2 requests (over tor, might be ridiculously slow).
    """
    if dom is None:
        resp = get(base_url, headers={'User-Agent': gen_useragent()})
        dom = fromstring(resp.text)
    name_token = extract_text(dom.xpath(name_token_xpath))
    value_token = extract_text(dom.xpath(value_token_xpath))
    return f"{name_token}:{value_token}"


def request(query, params):
    token_str: str | None = CACHE.get('ahmia-tokens')
    if not token_str:
        token_str = _get_tokens()
        CACHE.set('ahmia-tokens', token_str, expire=60 * 60)
    name_token, value_token = token_str.split(":")

    params['url'] = search_url.format(query=urlencode({'q': query, name_token: value_token}))

    if params['time_range'] in time_range_dict:
        params['url'] += '&' + urlencode({'d': time_range_dict[params['time_range']]})

    return params


def response(resp):
    results = []
    dom = fromstring(resp.text)

    # trim results so there's not way too many at once
    first_result_index = page_size * (resp.search_params.get('pageno', 1) - 1)
    all_results = eval_xpath_list(dom, results_xpath)
    trimmed_results = all_results[first_result_index : first_result_index + page_size]

    # get results
    for result in trimmed_results:
        # remove ahmia url and extract the actual url for the result
        raw_url = extract_url(eval_xpath_list(result, url_xpath, min_len=1), search_url)
        cleaned_url = parse_qs(urlparse(raw_url).query).get('redirect_url', [''])[0]

        title = extract_text(eval_xpath(result, title_xpath))
        content = extract_text(eval_xpath(result, content_xpath))

        results.append({'url': cleaned_url, 'title': title, 'content': content, 'is_onion': True})

    # get spelling corrections
    for correction in eval_xpath_list(dom, correction_xpath):
        results.append({'correction': extract_text(correction)})

    # get number of results
    number_of_results = eval_xpath(dom, number_of_results_xpath)
    if number_of_results:
        try:
            results.append({'number_of_results': int(extract_text(number_of_results))})
        except:  # pylint: disable=bare-except
            pass

    # Update the tokens to the newest ones
    token_str = _get_tokens(dom)
    CACHE.set('ahmia-tokens', token_str, expire=60 * 60)

    return results
