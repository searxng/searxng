# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tencent Cloud Web Search API Engine

This engine uses the Tencent Cloud Web Search API to provide high-quality web
search results with excellent Chinese language support. The API supports
multiple search modes, site filtering, time range filtering, and industry
filtering (premium tier only).

API Documentation: https://cloud.tencent.com/document/product/1806/121811
"""

import json
import time
import hmac
import hashlib
from datetime import datetime

# Engine metadata
about = {
    "website": "https://cloud.tencent.com/product/wsa",
    "wikidata_id": None,
    "official_api_documentation": "https://cloud.tencent.com/document/product/1806/121811",
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
}

# Engine configuration
engine_type = 'online'
categories = ['general', 'web']
paging = False
language_support = True
time_range_support = False
safesearch = False

# API configuration
base_url = 'https://wsa.tencentcloudapi.com'


def sign(key, msg):
    """Generate HMAC signature"""
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def get_signature_v3(secret_id, secret_key, host, payload, timestamp):  # pylint: disable=too-many-locals
    """Generate Tencent Cloud API v3 signature (TC3-HMAC-SHA256).
    
    Documentation: https://cloud.tencent.com/document/api/1806/121815
    """
    # Step 1: Build canonical request
    http_request_method = 'POST'
    canonical_uri = '/'
    canonical_querystring = ''
    canonical_headers = f'content-type:application/json\nhost:{host}\n'
    signed_headers = 'content-type;host'
    hashed_request_payload = hashlib.sha256(payload.encode('utf-8')).hexdigest()

    canonical_request = (
        f'{http_request_method}\n'
        f'{canonical_uri}\n'
        f'{canonical_querystring}\n'
        f'{canonical_headers}\n'
        f'{signed_headers}\n'
        f'{hashed_request_payload}'
    )

    # Step 2: Build string to sign
    algorithm = 'TC3-HMAC-SHA256'
    date = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')
    credential_scope = f'{date}/wsa/tc3_request'
    hashed_canonical_request = hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

    string_to_sign = (
        f'{algorithm}\n'
        f'{timestamp}\n'
        f'{credential_scope}\n'
        f'{hashed_canonical_request}'
    )

    # Step 3: Calculate signature
    secret_date = sign(f'TC3{secret_key}'.encode('utf-8'), date)
    secret_service = sign(secret_date, 'wsa')
    secret_signing = sign(secret_service, 'tc3_request')
    signature = hmac.new(secret_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    # Step 4: Build Authorization header
    authorization = (
        f'{algorithm} '
        f'Credential={secret_id}/{credential_scope}, '
        f'SignedHeaders={signed_headers}, '
        f'Signature={signature}'
    )

    return authorization


def request(query, params):
    """Build search request for Tencent Cloud API."""

    # Get configuration from engine_settings
    engine_settings = params.get('engine_settings', {})
    api_key = engine_settings.get('api_key', '')
    secret_key = engine_settings.get('secret_key', '')
    
    if not api_key or not secret_key:
        # If no API credentials configured, return empty results
        params['url'] = None
        return params

    # Get search mode (0=natural, 1=multimodal VR, 2=mixed)
    mode = engine_settings.get('mode', 0)
    
    # Build request body
    request_body = {
        'Query': query,
        'Mode': mode,
    }

    # Add optional parameters
    cnt = engine_settings.get('cnt', 10)
    if cnt > 10:
        request_body['Cnt'] = cnt

    site = engine_settings.get('site')
    if site:
        request_body['Site'] = site

    from_time = engine_settings.get('from_time')
    if from_time:
        request_body['FromTime'] = from_time

    to_time = engine_settings.get('to_time')
    if to_time:
        request_body['ToTime'] = to_time

    # Prepare request
    timestamp = int(time.time())
    host = 'wsa.tencentcloudapi.com'
    payload = json.dumps(request_body)

    # Generate signature
    authorization = get_signature_v3(api_key, secret_key, host, payload, timestamp)

    # Build request headers
    headers = {
        'Authorization': authorization,
        'Content-Type': 'application/json',
        'Host': host,
        'X-TC-Action': 'SearchPro',
        'X-TC-Version': '2025-05-08',
        'X-TC-Timestamp': str(timestamp),
        'X-TC-Region': '',
    }

    params['url'] = f'https://{host}/'
    params['method'] = 'POST'
    params['headers'] = headers
    params['data'] = payload

    return params


def response(resp):
    """Parse API response and return search results."""
    results = []

    try:
        data = resp.json()
    except json.JSONDecodeError:
        return results

    # Check response structure
    if 'Response' not in data:
        return results

    response_data = data['Response']

    # Check for API errors
    if 'Error' in response_data:
        error = response_data['Error']
        error_code = error.get('Code', 'Unknown')
        error_message = error.get('Message', 'Unknown error')
        raise ValueError(f"Tencent Cloud API error: {error_code} - {error_message}")

    # Parse search results
    pages = response_data.get('Pages', [])

    for page_str in pages:
        try:
            # Each page is a JSON string that needs to be parsed
            page = json.loads(page_str)

            url = page.get('url', '')
            title = page.get('title', '')
            
            if not url or not title:
                continue

            # Build result dictionary
            result = {
                'url': url,
                'title': title,
                'content': page.get('passage', page.get('content', '')),
            }

            # Add optional fields
            if 'date' in page:
                result['publishedDate'] = page['date']

            if 'site' in page:
                result['metadata'] = page['site']

            if 'images' in page and page['images']:
                if isinstance(page['images'], list):
                    result['img_src'] = page['images'][0]
                else:
                    result['img_src'] = page['images']

            if 'favicon' in page and page['favicon']:
                result['thumbnail'] = page['favicon']

            # Add relevance score to metadata
            if 'score' in page:
                metadata = result.get('metadata', '')
                score_info = f"Relevance: {page['score']:.2f}"
                result['metadata'] = f"{metadata} ({score_info})".strip()

            results.append(result)

        except (json.JSONDecodeError, KeyError):
            # Skip malformed results
            continue

    return results
