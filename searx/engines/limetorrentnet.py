"""LimeTorrents

"""

from urllib.parse import urlencode

from lxml import html

from searx.utils import (
    extract_text,
    eval_xpath,
)

about = {
    "website": 'https://limetorrent.net',
}
base_url = 'https://limetorrent.net'


def request(query, params):
    query_params = {
        'q': query,
    }
    params['url'] = f"{base_url}/search/?{urlencode(query_params)}"
    return params


def response(resp):
    results = []
    dom = html.fromstring(resp.text)

    for result in eval_xpath(dom, '//tbody/tr[@bgcolor="#F4F4F4"]'):
        title = result.xpath('.//td/div')
        title = extract_text(title[0]) if title else None

        url = result.xpath('.//td/div/a/@href')
        url = extract_text(url[0]) if url else None

        if url or title:
            results.append({'url': url, 'title': title, })
    return results
