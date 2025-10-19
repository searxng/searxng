# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tencent Cloud Web Search API Engine

This engine uses the Tencent Cloud Web Search API to provide high-quality web
search results with excellent Chinese language support. The API supports
multiple search modes, site filtering, time range filtering, and industry
filtering (premium tier only).

API Documentation: https://cloud.tencent.com/document/product/1806/121811

Configuration:
- timeout: Recommended 10-15 seconds (API response can be slow with large result counts)
- cnt: Number of results (10-50). Values >10 require premium tier and may increase response time

Usage with URL parameters:
You can override settings.yml configuration by passing parameters in the URL:
  
  ?q=your_query&engine_data-tencent-mode=2&engine_data-tencent-cnt=50&engine_data-tencent-site=xueqiu.com&engine_data-tencent-from_time=20180101&engine_data-tencent-to_time=20181231

URL Parameters:
- engine_data-tencent-mode: Search mode (0/1/2)
- engine_data-tencent-cnt: Number of results (10-50)
- engine_data-tencent-site: Site filter (e.g., xueqiu.com)
- engine_data-tencent-from_time: Start time (YYYYMMDD like 20180101, or Unix timestamp like 1514764800)
- engine_data-tencent-to_time: End time (YYYYMMDD like 20181231, or Unix timestamp like 1546300799)

Note: URL parameters take priority over settings.yml configuration.
"""

import json
import time
import hmac
import hashlib
from datetime import datetime, timezone

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
timeout = 10.0  # Tencent API can be slow, increase default timeout

# API configuration (set in settings.yml)
base_url = 'https://wsa.tencentcloudapi.com'
api_key = ''  # SecretId from Tencent Cloud (required)
secret_key = ''  # SecretKey from Tencent Cloud (required)

# Optional parameters (can be set in settings.yml):
# - mode: Search mode (0=natural, 1=multimodal VR, 2=mixed), default: 0
#     Note: mode=1 ignores time filters; mode=0 applies to all results; mode=2 applies to natural results
# - cnt: Number of results (10/20/30/40/50), default: 10
# - site: Site filter (e.g., "xueqiu.com")
# - from_time: Start time filter, supports two formats:
#     1. YYYYMMDD: e.g., 20180101 (will be converted to Unix timestamp at 00:00:00 UTC)
#     2. Unix timestamp: e.g., 1514764800 (seconds since epoch)
# - to_time: End time filter, supports two formats:
#     1. YYYYMMDD: e.g., 20181231 (will be converted to Unix timestamp at 23:59:59 UTC)
#     2. Unix timestamp: e.g., 1546300799 (seconds since epoch)
# 
# Example configuration:
#   - name: tencent
#     engine: tencent
#     api_key: 'YOUR_KEY'
#     secret_key: 'YOUR_SECRET'
#     mode: 2
#     cnt: 50
#     site: 'xueqiu.com'
#     from_time: 20180101      # YYYYMMDD format (auto-converted to timestamp)
#     to_time: 20181231        # or use Unix timestamp: 1546300799
#
# These are NOT defined as module variables to avoid "missing required attribute" errors.
# Use globals().get() with defaults in request function


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
    date = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d')
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
    
    # Check if API credentials are configured
    if not api_key or not secret_key:
        # If no API credentials configured, return empty results
        params['url'] = None
        return params
    
    # Get engine_data from URL parameters (takes priority over settings.yml)
    # URL format: ?q=test&engine_data-tencent-mode=2&engine_data-tencent-cnt=50
    engine_data = params.get('engine_data', {})
    
    # Get optional parameters: URL params override settings.yml config
    # Priority: URL params > settings.yml > defaults
    search_mode = int(engine_data.get('mode', globals().get('mode', 0)))
    result_count = int(engine_data.get('cnt', globals().get('cnt', 10)))
    site_filter = engine_data.get('site', globals().get('site'))
    start_time = engine_data.get('from_time', globals().get('from_time'))
    end_time = engine_data.get('to_time', globals().get('to_time'))
    
    # Build request body
    request_body = {
        'Query': query,
        'Mode': search_mode,
    }

    # Add result count (API default is 10, but we explicitly set it if different)
    if result_count != 10:
        request_body['Cnt'] = result_count

    # Add site filter
    if site_filter:
        request_body['Site'] = site_filter

    # Add time range parameters
    # API expects Unix timestamp (seconds since epoch)
    # Input can be:
    #   1. Unix timestamp (int): e.g., 1745498501
    #   2. YYYYMMDD format (int/str): e.g., 20180101 or "20180101" -> converted to timestamp
    if start_time:
        try:
            timestamp_val = int(start_time)
            # If value looks like YYYYMMDD (8 digits, < 100000000), convert to timestamp
            if timestamp_val < 100000000:
                # Parse as YYYYMMDD and convert to timestamp
                year = timestamp_val // 10000
                month = (timestamp_val % 10000) // 100
                day = timestamp_val % 100
                dt = datetime(year, month, day, 0, 0, 0, tzinfo=timezone.utc)
                request_body['FromTime'] = int(dt.timestamp())
            else:
                # Already a timestamp
                request_body['FromTime'] = timestamp_val
        except (ValueError, TypeError):
            pass  # Skip invalid time values

    if end_time:
        try:
            timestamp_val = int(end_time)
            # If value looks like YYYYMMDD (8 digits, < 100000000), convert to timestamp
            if timestamp_val < 100000000:
                # Parse as YYYYMMDD and convert to timestamp (end of day)
                year = timestamp_val // 10000
                month = (timestamp_val % 10000) // 100
                day = timestamp_val % 100
                dt = datetime(year, month, day, 23, 59, 59, tzinfo=timezone.utc)
                request_body['ToTime'] = int(dt.timestamp())
            else:
                # Already a timestamp
                request_body['ToTime'] = timestamp_val
        except (ValueError, TypeError):
            pass  # Skip invalid time values

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
                try:
                    # Parse date string to datetime object
                    # Format: "2025-10-04 05:00:47"
                    result['publishedDate'] = datetime.strptime(page['date'], '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    # If date parsing fails, skip this field
                    pass

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
