# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 Wolfram|Alpha (Science)
"""

from lxml import etree
from urllib.parse import urlencode

# about
about = {
    "website": 'https://www.wolframalpha.com',
    "wikidata_id": 'Q207006',
    "official_api_documentation": 'https://products.wolframalpha.com/api/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'XML',
}

# search-url
search_url = 'https://api.wolframalpha.com/v2/query?appid={api_key}&{query}'
site_url = 'https://www.wolframalpha.com/input/?{query}'
api_key = ''  # defined in settings.yml

# xpath variables
failure_xpath = '/queryresult[attribute::success="false"]'
input_xpath = '//pod[starts-with(attribute::id, "Input")]/subpod/plaintext'
pods_xpath = '//pod'
subpods_xpath = './subpod'
pod_primary_xpath = './@primary'
pod_id_xpath = './@id'
pod_title_xpath = './@title'
plaintext_xpath = './plaintext'
image_xpath = './img'
img_src_xpath = './@src'
img_alt_xpath = './@alt'

# pods to display as image in infobox
# this pods do return a plaintext, but they look better and are more useful as images
image_pods = {'VisualRepresentation', 'Illustration'}


# do search-request
def request(query, params):
    params['url'] = search_url.format(query=urlencode({'input': query}), api_key=api_key)
    params['headers']['Referer'] = site_url.format(query=urlencode({'i': query}))

    return params


# replace private user area characters to make text legible
def replace_pua_chars(text):
    pua_chars = {
        '\uf522': '\u2192',  # rigth arrow
        '\uf7b1': '\u2115',  # set of natural numbers
        '\uf7b4': '\u211a',  # set of rational numbers
        '\uf7b5': '\u211d',  # set of real numbers
        '\uf7bd': '\u2124',  # set of integer numbers
        '\uf74c': 'd',  # differential
        '\uf74d': '\u212f',  # euler's number
        '\uf74e': 'i',  # imaginary number
        '\uf7d9': '=',
    }  # equals sign

    for k, v in pua_chars.items():
        text = text.replace(k, v)

    return text


# get response from search-request
def response(resp):
    results = []

    search_results = etree.XML(resp.content)

    # return empty array if there are no results
    if search_results.xpath(failure_xpath):
        return []

    try:
        infobox_title = search_results.xpath(input_xpath)[0].text
    except:
        infobox_title = ""

    pods = search_results.xpath(pods_xpath)
    result_chunks = []
    result_content = ""
    for pod in pods:
        pod_id = pod.xpath(pod_id_xpath)[0]
        pod_title = pod.xpath(pod_title_xpath)[0]
        pod_is_result = pod.xpath(pod_primary_xpath)

        subpods = pod.xpath(subpods_xpath)
        if not subpods:
            continue

        # Appends either a text or an image, depending on which one is more suitable
        for subpod in subpods:
            content = subpod.xpath(plaintext_xpath)[0].text
            image = subpod.xpath(image_xpath)

            if content and pod_id not in image_pods:

                if pod_is_result or not result_content:
                    if pod_id != "Input":
                        result_content = "%s: %s" % (pod_title, content)

                # if no input pod was found, title is first plaintext pod
                if not infobox_title:
                    infobox_title = content

                content = replace_pua_chars(content)
                result_chunks.append({'label': pod_title, 'value': content})

            elif image:
                result_chunks.append(
                    {
                        'label': pod_title,
                        'image': {'src': image[0].xpath(img_src_xpath)[0], 'alt': image[0].xpath(img_alt_xpath)[0]},
                    }
                )

    if not result_chunks:
        return []

    title = "Wolfram Alpha (%s)" % infobox_title

    # append infobox
    results.append(
        {
            'infobox': infobox_title,
            'attributes': result_chunks,
            'urls': [{'title': 'Wolfram|Alpha', 'url': resp.request.headers['Referer']}],
        }
    )

    # append link to site
    results.append({'url': resp.request.headers['Referer'], 'title': title, 'content': result_content})

    return results
