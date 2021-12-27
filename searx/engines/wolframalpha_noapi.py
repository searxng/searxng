# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Wolfram|Alpha (Science)
"""

from json import loads
from time import time
from urllib.parse import urlencode

from searx.network import get as http_get

# about
about = {
    "website": 'https://www.wolframalpha.com/',
    "wikidata_id": 'Q207006',
    "official_api_documentation": 'https://products.wolframalpha.com/api/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

# search-url
url = 'https://www.wolframalpha.com/'

search_url = (
    url + 'input/json.jsp'
    '?async=false'
    '&banners=raw'
    '&debuggingdata=false'
    '&format=image,plaintext,imagemap,minput,moutput'
    '&formattimeout=2'
    '&{query}'
    '&output=JSON'
    '&parsetimeout=2'
    '&proxycode={token}'
    '&scantimeout=0.5'
    '&sponsorcategories=true'
    '&statemethod=deploybutton'
)

referer_url = url + 'input/?{query}'

token = {'value': '', 'last_updated': None}

# pods to display as image in infobox
# this pods do return a plaintext, but they look better and are more useful as images
image_pods = {'VisualRepresentation', 'Illustration', 'Symbol'}


# seems, wolframalpha resets its token in every hour
def obtain_token():
    update_time = time() - (time() % 3600)
    try:
        token_response = http_get('https://www.wolframalpha.com/input/api/v1/code?ts=9999999999999999999', timeout=2.0)
        token['value'] = loads(token_response.text)['code']
        token['last_updated'] = update_time
    except:
        pass
    return token


def init(engine_settings=None):
    obtain_token()


# do search-request
def request(query, params):
    # obtain token if last update was more than an hour
    if time() - (token['last_updated'] or 0) > 3600:
        obtain_token()
    params['url'] = search_url.format(query=urlencode({'input': query}), token=token['value'])
    params['headers']['Referer'] = referer_url.format(query=urlencode({'i': query}))

    return params


# get response from search-request
def response(resp):
    results = []

    resp_json = loads(resp.text)

    if not resp_json['queryresult']['success']:
        return []

    # TODO handle resp_json['queryresult']['assumptions']
    result_chunks = []
    infobox_title = ""
    result_content = ""
    for pod in resp_json['queryresult']['pods']:
        pod_id = pod.get('id', '')
        pod_title = pod.get('title', '')
        pod_is_result = pod.get('primary', None)

        if 'subpods' not in pod:
            continue

        if pod_id == 'Input' or not infobox_title:
            infobox_title = pod['subpods'][0]['plaintext']

        for subpod in pod['subpods']:
            if subpod['plaintext'] != '' and pod_id not in image_pods:
                # append unless it's not an actual answer
                if subpod['plaintext'] != '(requires interactivity)':
                    result_chunks.append({'label': pod_title, 'value': subpod['plaintext']})

                if pod_is_result or not result_content:
                    if pod_id != "Input":
                        result_content = pod_title + ': ' + subpod['plaintext']

            elif 'img' in subpod:
                result_chunks.append({'label': pod_title, 'image': subpod['img']})

    if not result_chunks:
        return []

    results.append(
        {
            'infobox': infobox_title,
            'attributes': result_chunks,
            'urls': [{'title': 'Wolfram|Alpha', 'url': resp.request.headers['Referer']}],
        }
    )

    results.append(
        {
            'url': resp.request.headers['Referer'],
            'title': 'Wolfram|Alpha (' + infobox_title + ')',
            'content': result_content,
        }
    )

    return results
