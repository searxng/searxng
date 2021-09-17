# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Yggtorrent (Videos, Music, Files)
"""

from lxml import html
from operator import itemgetter
from datetime import datetime
from urllib.parse import quote
from searx.utils import extract_text, get_torrent_size
from searx.network import get as http_get

# about
about = {
    "website": 'https://www4.yggtorrent.li/',
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['files']
paging = True

# search-url
url = 'https://www4.yggtorrent.li/'
search_url = url + 'engine/search?name={search_term}&do=search&page={pageno}&category={search_type}'

# yggtorrent specific type-definitions
search_types = {'files': 'all',
                'music': '2139',
                'videos': '2145'}

cookies = dict()


def init(engine_settings=None):
    # initial cookies
    resp = http_get(url, allow_redirects=False)
    if resp.ok:
        for r in resp.history:
            cookies.update(r.cookies)
        cookies.update(resp.cookies)


# do search-request
def request(query, params):
    search_type = search_types.get(params['category'], 'all')
    pageno = (params['pageno'] - 1) * 50

    params['url'] = search_url.format(search_term=quote(query),
                                      search_type=search_type,
                                      pageno=pageno)

    params['cookies'] = cookies

    return params


# get response from search-request
def response(resp):
    results = []
    dom = html.fromstring(resp.text)

    search_res = dom.xpath('//section[@id="#torrents"]/div/table/tbody/tr')

    # return empty array if nothing is found
    if not search_res:
        return []

    # parse results
    for result in search_res:
        link = result.xpath('.//a[@id="torrent_name"]')[0]
        href = link.attrib.get('href')
        title = extract_text(link)
        seed = result.xpath('.//td[8]/text()')[0]
        leech = result.xpath('.//td[9]/text()')[0]

        # convert seed to int if possible
        if seed.isdigit():
            seed = int(seed)
        else:
            seed = 0

        # convert leech to int if possible
        if leech.isdigit():
            leech = int(leech)
        else:
            leech = 0

        params = {'url': href,
                  'title': title,
                  'seed': seed,
                  'leech': leech,
                  'template': 'torrent.html'}

        # let's try to calculate the torrent size
        try:
            filesize_info = result.xpath('.//td[6]/text()')[0]
            filesize = filesize_info[:-2]
            filesize_multiplier = filesize_info[-2:].lower()
            multiplier_french_to_english = {
                'to': 'TiB',
                'go': 'GiB',
                'mo': 'MiB',
                'ko': 'KiB'
            }
            filesize = get_torrent_size(filesize, multiplier_french_to_english[filesize_multiplier])
            params['filesize'] = filesize
        except:
            pass

        # extract and convert creation date
        try:
            date_ts = result.xpath('.//td[5]/div/text()')[0]
            date = datetime.fromtimestamp(float(date_ts))
            params['publishedDate'] = date
        except:
            pass

        # append result
        results.append(params)

    # return results sorted by seeder
    return sorted(results, key=itemgetter('seed'), reverse=True)
