# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Youtube (Videos)
"""

from datetime import datetime
from functools import reduce
from json import loads, dumps
from urllib.parse import quote_plus

# about
about = {
    "website": 'https://www.youtube.com/',
    "wikidata_id": 'Q866',
    "official_api_documentation": 'https://developers.google.com/youtube/v3/docs/search/list?apix=true',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['videos', 'music']
paging = True
language_support = False
time_range_support = True

# search-url
base_url = 'https://www.youtube.com/results'
search_url = base_url + '?search_query={query}&page={page}'
time_range_url = '&sp=EgII{time_range}%253D%253D'
# the key seems to be constant
next_page_url = 'https://www.youtube.com/youtubei/v1/search?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
time_range_dict = {'day': 'Ag',
                   'week': 'Aw',
                   'month': 'BA',
                   'year': 'BQ'}

embedded_url = '<iframe width="540" height="304" ' +\
    'data-src="https://www.youtube-nocookie.com/embed/{videoid}" ' +\
    'frameborder="0" allowfullscreen></iframe>'

base_youtube_url = 'https://www.youtube.com/watch?v='


# do search-request
def request(query, params):
    if not params['engine_data'].get('next_page_token'):
        params['url'] = search_url.format(query=quote_plus(query), page=params['pageno'])
        if params['time_range'] in time_range_dict:
            params['url'] += time_range_url.format(time_range=time_range_dict[params['time_range']])
    else:
        params['url'] = next_page_url
        params['method'] = 'POST'
        params['data'] = dumps({
            'context': {"client": {"clientName": "WEB", "clientVersion": "2.20210310.12.01"}},
            'continuation': params['engine_data']['next_page_token'],
        })
        params['headers']['Content-Type'] = 'application/json'

    params['headers']['Cookie'] = "CONSENT=YES+cb.%s-17-p0.en+F+941;" % datetime.now().strftime("%Y%m%d")
    return params


# get response from search-request
def response(resp):
    if resp.search_params.get('engine_data'):
        return parse_next_page_response(resp.text)
    return parse_first_page_response(resp.text)


def parse_next_page_response(response_text):
    results = []
    result_json = loads(response_text)
    for section in (result_json['onResponseReceivedCommands'][0]
                    .get('appendContinuationItemsAction')['continuationItems'][0]
                    .get('itemSectionRenderer')['contents']):
        if 'videoRenderer' not in section:
            continue
        section = section['videoRenderer']
        content = "-"
        if 'descriptionSnippet' in section:
            content = ' '.join(x['text'] for x in section['descriptionSnippet']['runs'])
        results.append({
            'url': base_youtube_url + section['videoId'],
            'title': ' '.join(x['text'] for x in section['title']['runs']),
            'content': content,
            'author': section['ownerText']['runs'][0]['text'],
            'length': section['lengthText']['simpleText'],
            'template': 'videos.html',
            'embedded': embedded_url.format(videoid=section['videoId']),
            'thumbnail': section['thumbnail']['thumbnails'][-1]['url'],
        })
    try:
        token = result_json['onResponseReceivedCommands'][0]\
            .get('appendContinuationItemsAction')['continuationItems'][1]\
            .get('continuationItemRenderer')['continuationEndpoint']\
            .get('continuationCommand')['token']
        results.append({
            "engine_data": token,
            "key": "next_page_token",
        })
    except:
        pass

    return results


def parse_first_page_response(response_text):
    results = []
    results_data = response_text[response_text.find('ytInitialData'):]
    results_data = results_data[results_data.find('{'):results_data.find(';</script>')]
    results_json = loads(results_data) if results_data else {}
    sections = results_json.get('contents', {})\
                           .get('twoColumnSearchResultsRenderer', {})\
                           .get('primaryContents', {})\
                           .get('sectionListRenderer', {})\
                           .get('contents', [])

    for section in sections:
        if "continuationItemRenderer" in section:
            next_page_token = section["continuationItemRenderer"]\
                .get("continuationEndpoint", {})\
                .get("continuationCommand", {})\
                .get("token", "")
            if next_page_token:
                results.append({
                    "engine_data": next_page_token,
                    "key": "next_page_token",
                })
        for video_container in section.get('itemSectionRenderer', {}).get('contents', []):
            video = video_container.get('videoRenderer', {})
            videoid = video.get('videoId')
            if videoid is not None:
                url = base_youtube_url + videoid
                thumbnail = 'https://i.ytimg.com/vi/' + videoid + '/hqdefault.jpg'
                title = get_text_from_json(video.get('title', {}))
                content = get_text_from_json(video.get('descriptionSnippet', {}))
                embedded = embedded_url.format(videoid=videoid)
                author = get_text_from_json(video.get('ownerText', {}))
                length = get_text_from_json(video.get('lengthText', {}))

                # append result
                results.append({'url': url,
                                'title': title,
                                'content': content,
                                'author': author,
                                'length': length,
                                'template': 'videos.html',
                                'embedded': embedded,
                                'thumbnail': thumbnail})

    # return results
    return results


def get_text_from_json(element):
    if 'runs' in element:
        return reduce(lambda a, b: a + b.get('text', ''), element.get('runs'), '')
    else:
        return element.get('simpleText', '')
