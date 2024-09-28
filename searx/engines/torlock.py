from lxml import html
from searx.utils import (
    extract_text,
    eval_xpath,
)

about = {
    "website": 'https://www.torlock.com',
}
base_url = 'https://www.torlock.com'
paging = True


def request(query, params):
    params['url'] = f"{base_url}/all/torrents/{query}/{params.get('pageno', 1)}.html"
    return params


def response(resp):
    results = []
    dom = html.fromstring(resp.text)

    for result in eval_xpath(dom, '(.//tr)'):
        url_elem = result.xpath('.//div[@style="float:left"]/a/@href')
        if url_elem:
            url = url_elem[0]
            if not (url.startswith("www") or url.startswith("http")):
                url = f"{base_url}{url}"
            else:
                url = None
        else:
            url = None

        title_elem = result.xpath('.//div[@style="float:left"]/a/b')
        title = extract_text(title_elem[0]) if title_elem else None

        if title and url:
            results.append({
                'url': url,
                'title': title,
            })

    return results
