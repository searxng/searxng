# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""
Ghat GPT
"""

import json
import re
import requests
from urllib.parse import quote
import uuid

# about
about = {
    "website": 'https://chat.openai.com/chat',
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

USERNAME = ""
PASSWORD = ""
TOKEN_CACHE = ""


def get_authorization_token(invalidate: bool = False):
    global TOKEN_CACHE
    if TOKEN_CACHE is not None and not invalidate:
        return TOKEN_CACHE

    username = quote(USERNAME)
    password = quote(PASSWORD)

    session = requests.Session()

    # request 1. get cookies
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://openai.com/blog/chatgpt/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-User": "?1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers"
    }
    response = session.get('https://chat.openai.com/auth/login', headers=headers)
    if response.status_code != 200:
        raise Exception(f"Auth error in request 1. Response: {response.text}")

    # request 2. get csrf
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://chat.openai.com/auth/login",
        "DNT": "1",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers"
    }
    response = session.get("https://chat.openai.com/api/auth/csrf", headers=headers)
    if response.status_code != 200:
        raise Exception(f"Auth error in request 2. Response: {response.text}")
    csrf_token = response.json()["csrfToken"]

    # request 3. get login url
    url = "https://chat.openai.com/api/auth/signin/auth0"
    querystring = {"prompt": "login"}
    # todo: better encoding
    payload = f"callbackUrl=%2F&csrfToken={csrf_token}&json=true"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://chat.openai.com/auth/login",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://chat.openai.com",
        "DNT": "1",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers"
    }
    response = session.post(url, data=payload, params=querystring, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Auth error in request 3. Response: {response.text}")
    login_url = response.json()["url"]

    # request 4. get login form/state
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Alt-Used": "auth0.openai.com",
        "Connection": "keep-alive",
        "Referer": "https://chat.openai.com/",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-User": "?1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache"
    }
    response = session.get(login_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Auth error in request 4. Response: {response.text}")
    # todo: replace regular expression with html parser
    matches = re.search("name=\"state\" value=\"([^\"]+)\"", response.text)
    if len(matches.groups()) != 1:
        raise Exception(f"Auth error in request 4. State not found in the response")
    state = matches.groups()[0]

    # request 5. get login user
    url = "https://auth0.openai.com/u/login/identifier"
    querystring = {
        "state": state
    }
    payload = f"state={state}&username={username}&js-available=true&webauthn-available=true&is-brave=false&webauthn-platform-available=false&action=default"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": response.url,
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://auth0.openai.com",
        "DNT": "1",
        "Alt-Used": "auth0.openai.com",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache"
    }
    response = session.post(url, data=payload, headers=headers, params=querystring)
    if response.status_code != 200:
        raise Exception(f"Auth error in request 5. Response: {response.text}")

    # request 6. get login password
    url = "https://auth0.openai.com/u/login/password"
    querystring = {
        "state": state
    }
    payload = f"state={state}&username={username}&password={password}&action=default"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": response.url,
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://auth0.openai.com",
        "DNT": "1",
        "Alt-Used": "auth0.openai.com",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache"
    }
    response = session.post(url, data=payload, headers=headers, params=querystring)
    if response.status_code != 200:
        raise Exception(f"Auth error in request 6. Response: {response.text}")

    # request 6. get jwt token
    url = "https://chat.openai.com/api/auth/session"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://chat.openai.com/chat",
        "DNT": "1",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers"
    }
    response = session.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Auth error in request 7. Response: {response.text}")
    TOKEN_CACHE = response.json()["accessToken"]
    return TOKEN_CACHE


def send_request(query: str, token: str):
    url = "https://chat.openai.com/backend-api/conversation"
    # todo: generate random uuid
    payload = {
        "action": "next",
        "messages": [
            {
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": {
                    "content_type": "text",
                    "parts": [query]
                }
            }
        ],
        "parent_message_id": str(uuid.uuid4()),
        "model": "text-davinci-002-render"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0",
        "Accept": "text/event-stream",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://chat.openai.com/chat",
        "Content-Type": "application/json",
        "X-OpenAI-Assistant-App-Id": "",
        "Authorization": f"Bearer {token}",
        "Origin": "https://chat.openai.com",
        "DNT": "1",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache"
    }
    response = requests.request("POST", url, json=payload, headers=headers)
    payload_str = response.text

    try:
        last_item = payload_str.split('data:')[-2]
        text_items = json.loads(last_item)['message']['content']['parts']
        text = '\n'.join(text_items)
        return text.replace(r'\n+', '\n')
    except IndexError:
        error_message = json.loads(payload_str)['detail']
        raise Exception(error_message)


def request(query, params):
    # todo: the requests are working but the response method is never called
    # todo: we have to cache get_authorization_token()
    """build request"""
    # params['url'] = "https://chat.openai.com/backend-api/conversation"
    # params['method'] = 'POST'
    # params['data'] = {
    #     "action": "next",
    #     "messages": [
    #         {
    #             "id": str(uuid.uuid4()),
    #             "role": "user",
    #             "content": {
    #                 "content_type": "text",
    #                 "parts": [query]
    #             }
    #         }
    #     ],
    #     "parent_message_id": str(uuid.uuid4()),
    #     "model": "text-davinci-002-render"
    # }
    # params['headers'] = {
    #     "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0",
    #     "Accept": "text/event-stream",
    #     "Accept-Language": "en-US,en;q=0.5",
    #     "Accept-Encoding": "gzip, deflate, br",
    #     "Referer": "https://chat.openai.com/chat",
    #     "Content-Type": "application/json",
    #     "X-OpenAI-Assistant-App-Id": "",
    #     "Authorization": f"Bearer {token}",
    #     "Origin": "https://chat.openai.com",
    #     "DNT": "1",
    #     "Connection": "keep-alive",
    #     "Sec-Fetch-Dest": "empty",
    #     "Sec-Fetch-Mode": "cors",
    #     "Sec-Fetch-Site": "same-origin",
    #     "Pragma": "no-cache",
    #     "Cache-Control": "no-cache"
    # }

    # fake request for now
    params['query'] = query
    params['url'] = "https://www.google.com"
    params['engine_data']['token'] = "aaaa"
    return params


def response(resp):
    """parse response"""
    token = get_authorization_token()
    try:
        content = send_request(resp.search_params['query'], token)
    except:
        token = get_authorization_token(True)
        content = send_request(resp.search_params['query'], token)

    results = [
        {
            'infobox': 'Chat GPT',
            'content': content,
        }
    ]
    return results
