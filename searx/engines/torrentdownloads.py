from lxml import html
from searx.utils import (
    extract_text,
    eval_xpath,
)

about = {
    "website": 'https://www.torrentdownloads.pro',
}
base_url = 'https://www.torrentdownloads.pro'


def request(query, params):
    params['url'] = f"{base_url}/search/?search={query}"
    return params


def response(resp):
    results = []
    dom = html.fromstring(resp.text)

    for result in eval_xpath(dom, '(//div[@class="inner_container"])[2]/div[contains(@class, "grey_bar3")]'):
        url_elem = result.xpath('.//p/a/@href')
        url = url_elem[0] if url_elem else None

        if url and not (url.startswith('www') or url.startswith('http')):
            url = f"{base_url}{url}"

        title_elem = result.xpath('.//p/a')
        title = extract_text(title_elem[0]) if title_elem else None

        if title and url:
            results.append({
                'url': url,
                'title': title,
            })

    return results
