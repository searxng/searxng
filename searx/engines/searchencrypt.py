from urllib.parse import urlencode
from lxml import html
from searx.utils import extract_text

about = {
    "website": 'https://www.searchencrypt.com',
    "results": 'HTML',
}

safesearch = True
base_url = 'https://www.searchencrypt.com/search'

def request(query, params):
    query_params = {
        'q': query,
    }

    params['url'] = f'{base_url}?{urlencode(query_params)}'
    return params

def response(resp):
    results = []
    dom = html.fromstring(resp.text)

    # Update XPath expressions based on provided HTML structure
    for result in dom.xpath('//div[@class="serp__web-result__container"]'):
        link = result.xpath('.//div/h3/a/@href')
        link = link[0] if link else None

        title = result.xpath('.//div/h3/a/span')
        title = extract_text(title[0]) if title else None

        content = result.xpath('.//div/p/a/span')
        content = extract_text(content[0]) if content else 'None'

        if link or title or content:
            results.append({'url': link, 'title': title, 'content': content})

    return results
