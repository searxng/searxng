from lxml import html
from searx.utils import (
    extract_text,
    eval_xpath,
)

about = {
    "website": 'https://www.limetorrents.lol',
}
base_url = 'https://www.limetorrents.lol'


def request(query, params):
    params['url'] = f"{base_url}/search/all/{query}/"
    return params


def response(resp):
    results = []
    dom = html.fromstring(resp.text)

    for result in eval_xpath(dom,
                             '//table[@class="table2"]//tr[@bgcolor="#F4F4F4"] | //table[@class="table2"]//tr[@bgcolor="#FFFFFF"]'):
        title = result.xpath('.//td/div')
        title = extract_text(title[0]) if title else None

        url = result.xpath('.//td/div/a/@href')
        url = url[0] if url else None


        if url or title:
            results.append({'url': url, 'title': title,})

    return results
