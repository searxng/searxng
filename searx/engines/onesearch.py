# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint

"""OneSearch (Yahoo & Verizon)

- https://www.onesearch.com

OneSearch is literally just Bing results flanked by ads that don’t track you
despite being from a company that makes money tracking you [1].

According to the OneSearch privacy policy, search results will only be
personalized based on location, which it will collect from IP addresses.
OneSearch says that it will separate IP addresses from users and their search
results [2].

[1] https://lifehacker.com/is-yahoos-new-onesearch-engine-good-for-privacy-1841042875
[2] https://www.theverge.com/2020/1/14/21065640/verizon-onesearch-privacy-tracking-yahoo-breach-hack
"""

import re
from urllib.parse import unquote
from lxml.html import fromstring
from searx.utils import (
    eval_xpath,
    extract_text,
)

about = {
    "website": 'https://www.onesearch.com',
    "wikidata_id": 'Q109682354',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['general']
paging = True

URL = 'https://www.onesearch.com/yhs/search;?p=%s&b=%d'

def request(query, params):
    starting_from = (params['pageno'] * 10) - 9
    params['url'] = URL % (query, starting_from)
    return params

def response(resp):

    results = []
    doc = fromstring(resp.text)

    titles_tags = eval_xpath(
        doc, '//div[contains(@class, "algo")]//h3[contains(@class, "title")]')
    contents = eval_xpath(
        doc, '//div[contains(@class, "algo")]/div[contains(@class, "compText")]/p')
    onesearch_urls = eval_xpath(
        doc, '//div[contains(@class, "algo")]//h3[contains(@class, "title")]/a/@href')

    for title_tag, content, onesearch_url in zip(titles_tags, contents, onesearch_urls):
        matches = re.search(r'RU=(.*?)\/', onesearch_url)
        results.append({
            'title': title_tag.text_content(),
            'content': extract_text(content),
            'url': unquote(matches.group(1)),
        })

    return results
