from urllib.parse import urlencode
from lxml import html
from searx.utils import extract_text

about = {
    "website": 'https://www.sogou.com/',
    "results": 'HTML',
}

paging = True
base_url = 'https://www.sogou.com/web'


def request(query, params):
    page = params.get('pageno', 1)
    query_params = {
        'query': query,
        'page': page,
    }

    # Add the URL for the request
    params['url'] = f'{base_url}?{urlencode(query_params)}'

    # Custom headers for the request
    headers = {
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Origin': 'https://translate.sogou.com',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': 'application/json',
        'Referer': 'https://translate.sogou.com/',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
    }

    # Merge with any existing headers in params
    if 'headers' in params:
        params['headers'].update(headers)
    else:
        params['headers'] = headers

    return params


def response(resp):
    results = []
    dom = html.fromstring(resp.text)

    for result in dom.xpath('//div[@class="vrwrap"]'):
        # Extract link
        link_divs = result.xpath('.//div[contains(@class, "r-sech") and (contains(@class, "click-better-sugg") or contains(@class, "result_list"))]')
        link = link_divs[0].xpath('./@data-url')[0] if link_divs else None

        # Extract title
        title_elem = result.xpath('.//h3[@class="vr-title"]/a') or result.xpath('.//div/h3/a')
        title = title_elem[0].text_content().strip() if title_elem else None

        # Extract content from multiple possible elements
        content_elem = result.xpath('.//div[@class="fz-mid space-txt"]')
        content = content_elem[0].text_content().strip() if content_elem else 'None'

        if link or title:
            results.append({
                'url': link,
                'title': title,
                'content': content,
            })
    return results

