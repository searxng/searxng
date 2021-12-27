# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 BTDigg (Videos, Music, Files)
"""

from lxml import html
from urllib.parse import quote, urljoin
from searx.utils import extract_text, get_torrent_size

# about
about = {
    "website": 'https://btdig.com',
    "wikidata_id": 'Q4836698',
    "official_api_documentation": {'url': 'https://btdig.com/contacts', 'comment': 'on demand'},
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['files']
paging = True

# search-url
url = 'https://btdig.com'
search_url = url + '/search?q={search_term}&p={pageno}'


# do search-request
def request(query, params):
    params['url'] = search_url.format(search_term=quote(query), pageno=params['pageno'] - 1)

    return params


# get response from search-request
def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    search_res = dom.xpath('//div[@class="one_result"]')

    # return empty array if nothing is found
    if not search_res:
        return []

    # parse results
    for result in search_res:
        link = result.xpath('.//div[@class="torrent_name"]//a')[0]
        href = urljoin(url, link.attrib.get('href'))
        title = extract_text(link)

        excerpt = result.xpath('.//div[@class="torrent_excerpt"]')[0]
        content = html.tostring(excerpt, encoding='unicode', method='text', with_tail=False)
        # it is better to emit <br/> instead of |, but html tags are verboten
        content = content.strip().replace('\n', ' | ')
        content = ' '.join(content.split())

        filesize = result.xpath('.//span[@class="torrent_size"]/text()')[0].split()[0]
        filesize_multiplier = result.xpath('.//span[@class="torrent_size"]/text()')[0].split()[1]
        files = (result.xpath('.//span[@class="torrent_files"]/text()') or ['1'])[0]

        # convert filesize to byte if possible
        filesize = get_torrent_size(filesize, filesize_multiplier)

        # convert files to int if possible
        try:
            files = int(files)
        except:
            files = None

        magnetlink = result.xpath('.//div[@class="torrent_magnet"]//a')[0].attrib['href']

        # append result
        results.append(
            {
                'url': href,
                'title': title,
                'content': content,
                'filesize': filesize,
                'files': files,
                'magnetlink': magnetlink,
                'template': 'torrent.html',
            }
        )

    # return results sorted by seeder
    return results
