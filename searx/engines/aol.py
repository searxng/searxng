from urllib.parse import urlencode
from lxml import html
from searx.utils import extract_text

about = {
    "website": 'https://search.aol.com',
    "results": 'HTML',
}

safesearch = True
paging = True
base_url = 'https://search.aol.com/aol/search'
pz = 10


def request(query, params):
    page = ((params['pageno'] - 1) * pz) + 1

    safesearch = 'i' if params['safesearch'] == '1' else 'r' if params['safesearch'] == '2' else 'p'

    query_params = {
        'q': query,
        'b': page,
        'pz': pz
    }

    params['url'] = f'{base_url}?{urlencode(query_params)}'
    params['headers']['Cookie'] = f"sB={safesearch}"
    return params


def response(resp):
    results = []
    dom = html.fromstring(resp.text)

    for result in dom.xpath('//li//div[contains(@class, "algo")]'):
        link = result.xpath('.//h3/a/@href')
        link = link[0] if link else None

        title = result.xpath('.//h3/a')
        title = extract_text(title[0]) if title else None

        content = result.xpath('.//div[contains(@class, "compText")]//p')
        content = extract_text(content) if content else None

        extra_url_elements = result.xpath('.//div//span[contains(@class, "fz-ms fw-m fc-12th wr-bw lh-17")]')
        extra_url_element = extract_text(extra_url_elements[0]) if extra_url_elements else None

        if extra_url_element and not extra_url_element.endswith("..."):
            link = f'https://{extra_url_element}'

        if link or title or content:
            results.append({'url': link, 'title': title, 'content': content})

    return results
