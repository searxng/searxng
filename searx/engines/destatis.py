# SPDX-License-Identifier: AGPL-3.0-or-later
"""DeStatis
"""

from urllib.parse import urlencode
from lxml import html
from searx.utils import eval_xpath, eval_xpath_list, extract_text

about = {
    'website': 'https://www.destatis.de',
    'official_api_documentation': 'https://destatis.api.bund.dev/',
    'use_official_api': False,
    'require_api_key': False,
    'results': 'HTML',
    'language': 'de',
}

categories = []
paging = True

base_url = "https://www.destatis.de"
search_url = f"{base_url}/SiteGlobals/Forms/Suche/Expertensuche_Formular.html"

# pylint: disable-next=line-too-long
results_xpath = '//div[contains(@class, "l-content-wrapper")]/div[contains(@class, "row")]/div[contains(@class, "column")]/div[contains(@class, "c-result"){extra}]'
results_xpath_filter_recommended = " and not(contains(@class, 'c-result--recommended'))"
url_xpath = './/a/@href'
title_xpath = './/a/text()'
date_xpath = './/a/span[contains(@class, "c-result__date")]'
content_xpath = './/div[contains(@class, "column")]/p/text()'
doctype_xpath = './/div[contains(@class, "c-result__doctype")]/p'


def request(query, params):
    args = {
        'templateQueryString': query,
        'gtp': f"474_list%3D{params['pageno']}",
    }
    params['url'] = f"{search_url}?{urlencode(args)}"
    return params


def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    # filter out suggested results on further page because they're the same on each page
    extra_xpath = results_xpath_filter_recommended if resp.search_params['pageno'] > 1 else ''
    res_xpath = results_xpath.format(extra=extra_xpath)

    for result in eval_xpath_list(dom, res_xpath):
        doctype = extract_text(eval_xpath(result, doctype_xpath))
        date = extract_text(eval_xpath(result, date_xpath))

        metadata = [meta for meta in (doctype, date) if meta != ""]

        results.append(
            {
                'url': base_url + "/" + extract_text(eval_xpath(result, url_xpath)),
                'title': extract_text(eval_xpath(result, title_xpath)),
                'content': extract_text(eval_xpath(result, content_xpath)),
                'metadata': ', '.join(metadata),
            }
        )

    return results
