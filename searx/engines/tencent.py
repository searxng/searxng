# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tencent Cloud Web Search API Engine

Tencent Cloud Web Search API provides high-quality web search with excellent
Chinese language support.

API Documentation: https://cloud.tencent.com/document/product/1806/121811
"""

import json
import time
import hmac
import hashlib
from datetime import datetime

# Engine metadata
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
    """
    Generate Tencent Cloud API v3 signature (TC3-HMAC-SHA256)
    Documentation: https://cloud.tencent.com/document/api/1806/121815
    """
    # 1. Build canonical request
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

    # 2. Build string to sign
    algorithm = 'TC3-HMAC-SHA256'
    date = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')
    credential_scope = f'{date}/wsa/tc3_request'
    hashed_canonical_request = hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

    string_to_sign = f'{algorithm}\n' f'{timestamp}\n' f'{credential_scope}\n' f'{hashed_canonical_request}'

    # 3. Calculate signature
    secret_date = sign(f'TC3{secret_key}'.encode('utf-8'), date)
    secret_service = sign(secret_date, 'wsa')
    secret_signing = sign(secret_service, 'tc3_request')
    signature = hmac.new(secret_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    # 4. Build Authorization header
    authorization = (
        f'{algorithm} '
        f'Credential={secret_id}/{credential_scope}, '
        f'SignedHeaders={signed_headers}, '
        f'Signature={signature}'
    )

    return authorization


def request(query, params):
    """Handle search request"""

    # Get configuration from engine_settings
    engine_settings = params.get('engine_settings', {})
    api_key = engine_settings.get('api_key', '')
    secret_key_param = engine_settings.get('secret_key', '')
    mode = engine_settings.get('mode', 0)  # 0=natural search results (default)
    cnt = engine_settings.get('cnt', 10)  # Number of results to return

    if not api_key or not secret_key_param:
        # If no API key configured, return empty results
        params['url'] = None
        return params

    # Prepare request parameters
    timestamp = int(time.time())
    host = 'wsa.tencentcloudapi.com'

    # Build request body
    request_body = {'Query': query, 'Mode': mode}

    # Add optional parameters
    if cnt and cnt > 10:
        request_body['Cnt'] = cnt

    # Add site filtering if specified
    site = engine_settings.get('site', '')
    if site:
        request_body['Site'] = site

    payload = json.dumps(request_body)

    # Generate signature
    authorization = get_signature_v3(api_key, secret_key_param, host, payload, timestamp)

    # Build request headers
    headers = {
        'Authorization': authorization,
        'Content-Type': 'application/json',
        'Host': host,
        'X-TC-Action': 'SearchPro',
        'X-TC-Version': '2025-05-08',
        'X-TC-Timestamp': str(timestamp),
        'X-TC-Region': '',  # Region not required
    }

    # Send request
    params['url'] = f'https://{host}/'
    params['method'] = 'POST'
    params['headers'] = headers
    params['data'] = payload

    return params


def response(resp):  # pylint: disable=too-many-branches
    """Handle API response"""
    results = []

    try:
        data = json.loads(resp.text)

        # Check for response structure
        if 'Response' not in data:
            return results

        response_data = data['Response']

        # Check for API errors
        if 'Error' in response_data:
            error = response_data['Error']
            error_code = error.get('Code', 'Unknown')
            error_message = error.get('Message', 'Unknown error')
            error_msg = f"Tencent Cloud API error: {error_code} - {error_message}"
            raise ValueError(error_msg)

        # Parse search results
        pages = response_data.get('Pages', [])

        for page_str in pages:
            try:
                # Each page is a JSON string
                page = json.loads(page_str)

                result = {
                    'url': page.get('url', ''),
                    'title': page.get('title', ''),
                    'content': page.get('passage', page.get('content', '')),
                }

                # Add optional fields
                if 'date' in page:
                    result['publishedDate'] = page['date']

                if 'site' in page:
                    result['metadata'] = page['site']

                if 'images' in page and page['images']:
                    result['img_src'] = page['images'][0] if isinstance(page['images'], list) else page['images']

                # Add thumbnail/favicon
                if 'favicon' in page and page['favicon']:
                    result['thumbnail'] = page['favicon']

                # Add relevance score if available
                if 'score' in page:
                    result['metadata'] = f"{result.get('metadata', '')} (Relevance: {page['score']:.2f})".strip()

                if result['url'] and result['title']:
                    results.append(result)

            except (json.JSONDecodeError, KeyError):
                # Skip malformed results
                continue

    except json.JSONDecodeError:
        return results
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f'Tencent Cloud Search API error: {str(exc)}') from exc

    return results
