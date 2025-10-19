# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tencent Cloud Web Search API Engine

Tencent Cloud Web Search API provides high-quality web search with excellent
Chinese language support.

API Documentation: https://cloud.tencent.com/document/product/1806/121811

Configuration
=============

All parameters from the official API documentation are supported:

Required:
  - api_key (SecretId): Your Tencent Cloud API Secret ID
  - secret_key: Your Tencent Cloud API Secret Key

Optional:
  - mode (int): Result type
      * 0 = Natural search results (default)
      * 1 = Multimodal VR results
      * 2 = Mixed results (VR + natural)
  - cnt (int): Number of results to return (10/20/30/40/50)
      * Default: 10
      * Values > 10 require Premium edition
  - site (str): Domain-specific search (e.g., "zhihu.com")
      * Only effective in mode=0 or mode=2
  - from_time (int): Start time filter (Unix timestamp in seconds)
      * Only effective in mode=0 or mode=2
  - to_time (int): End time filter (Unix timestamp in seconds)
      * Only effective in mode=0 or mode=2
  - industry (str): Industry filter (Premium edition only)
      * "gov" = Government agencies
      * "news" = Authoritative media
      * "acad" = Academic sources

Example Configuration (settings.yml):

.. code:: yaml

  - name: tencent
    engine: tencent
    shortcut: tc
    disabled: false
    api_key: 'YOUR_SECRET_ID'
    secret_key: 'YOUR_SECRET_KEY'
    mode: 0
    cnt: 10
    # Optional filters
    # site: 'zhihu.com'
    # from_time: 1745498501
    # to_time: 1745584901
    # industry: 'news'

Usage
=====

Parameter Usage
---------------

All parameters are configured in settings.yml and automatically applied by the engine.
Users do not need to manually specify parameters when searching.

1. **Basic Search**:
   Enter in search box: ``!tc keyword``
   
   Example: ``!tc artificial intelligence``

2. **Site-Specific Search**:
   After configuring ``site: 'zhihu.com'``, all searches are automatically limited to Zhihu
   
   Search: ``!tc machine learning`` → Only returns results from Zhihu

3. **Time Filtering**:
   After configuring ``from_time`` and ``to_time``, automatically filters content within the specified time range
   
   Note: Requires Unix timestamp in seconds
   
   Python conversion example:
   ```python
   from datetime import datetime
   # 2025-01-01 00:00:00
   timestamp = int(datetime(2025, 1, 1).timestamp())
   ```

4. **Industry Filtering** (Premium edition):
   After configuring ``industry: 'news'``, automatically returns only authoritative media sources

5. **Multimodal Search**:
   After configuring ``mode: 1``, returns VR results combining images and text

Multiple Engine Instances
-------------------------

You can configure multiple engine instances for different purposes:

.. code:: yaml

  engines:
    # General search
    - name: tencent
      engine: tencent
      shortcut: tc
      api_key: 'xxx'
      secret_key: 'xxx'
    
    # Zhihu-specific search
    - name: tencent_zhihu
      engine: tencent
      shortcut: tczh
      api_key: 'xxx'
      secret_key: 'xxx'
      site: 'zhihu.com'
    
    # News search (authoritative media)
    - name: tencent_news
      engine: tencent
      shortcut: tcnews
      categories: [news]
      api_key: 'xxx'
      secret_key: 'xxx'
      industry: 'news'
      cnt: 20

Then use different shortcuts when searching:
- ``!tc keyword`` - General search
- ``!tczh keyword`` - Search within Zhihu
- ``!tcnews keyword`` - Authoritative media news

Combining Parameters
--------------------

Multiple parameters can be combined for precise search results:

.. code:: yaml

  - name: tencent_academic_recent
    engine: tencent
    shortcut: tcacad
    api_key: 'xxx'
    secret_key: 'xxx'
    mode: 0
    industry: 'acad'      # Academic sources only
    from_time: 1735660800 # 2025-01-01
    cnt: 30               # More results
    
Search: ``!tcacad quantum computing`` → Returns academic content after 2025

Parameter Effectiveness Scope
------------------------------

Note: Some parameters are only effective in specific modes

.. list-table::
   :header-rows: 1
   :widths: 20 20 20 20

   * - Parameter
     - mode=0 (Natural)
     - mode=1 (VR)
     - mode=2 (Mixed)
   * - Site
     - ✓
     - ✗
     - ✓ (natural part only)
   * - FromTime
     - ✓
     - ✗
     - ✓ (natural part only)
   * - ToTime
     - ✓
     - ✗
     - ✓ (natural part only)
   * - Industry
     - ✓
     - ✗
     - ✓ (natural part only)
   * - Cnt
     - ✓
     - ✓
     - ✓

Dynamic Parameter Support
--------------------------

**1. Site-Specific Search - Query Syntax**:

In addition to static configuration in settings.yml, users can dynamically specify sites when searching:

**Using site: syntax**:

.. code:: text

   !tc Python tutorial site:zhihu.com
   !tc code examples site:github.com
   !tc tech articles site:csdn.net

The engine automatically recognizes ``site:`` syntax and applies site filtering.

**Priority**: site: syntax in query > URL parameters > static settings in config file

**Example**:

.. code:: yaml

   # Configure general engine (without static site)
   - name: tencent
     engine: tencent
     shortcut: tc
     api_key: 'xxx'
     secret_key: 'xxx'

When searching:

- ``!tc Python`` - Search all websites
- ``!tc Python site:zhihu.com`` - Search Zhihu only
- ``!tc Python site:github.com`` - Search GitHub only
- ``!tc Python site:stackoverflow.com`` - Search StackOverflow only

**2. Time Range Selection - Interface Selector**:

In addition to static ``from_time`` and ``to_time`` settings in config file, users can
dynamically select time range in the search interface:

1. Enter in search box: ``!tc keyword``
2. Select time range in interface dropdown:
   - Anytime
   - Past day
   - Past week
   - Past month
   - Past year
3. Click search

The engine automatically converts the interface selection to corresponding timestamp parameters.

**Priority**: Interface time range selection > static time settings in config file

**Example 1: Fully Dynamic (Recommended)**:

.. code:: yaml

  # Configure general engine without any filters
  - name: tencent
    engine: tencent
    shortcut: tc
    api_key: 'xxx'
    secret_key: 'xxx'
    # Do not set site, from_time/to_time for maximum flexibility

Search examples:

- ``!tc Python`` + select ``Past week`` in interface - All websites, past week
- ``!tc Python site:github.com`` - GitHub, all time
- ``!tc Python site:zhihu.com`` + select ``Past month`` - Zhihu, past month

**Example 2: Combining Dynamic Parameters**:

.. code:: text

   !tc machine learning site:zhihu.com
   # Then select "Past month" in interface
   # Effect: Search machine learning content on Zhihu from the past month

   !tc React hooks site:github.com
   # Then select "Past year" in interface
   # Effect: Search React hooks related code on GitHub from the past year

**Example 3: Overriding Static Configuration**:

.. code:: yaml

  # Configure Zhihu-specific search (static site)
  - name: tencent_zhihu
    engine: tencent
    shortcut: tczh
    api_key: 'xxx'
    secret_key: 'xxx'
    site: 'zhihu.com'  # Static default value

When searching:

- ``!tczh Python`` - Search Zhihu (using static config)
- ``!tczh Python site:github.com`` - Search GitHub (dynamic overrides static)

This provides convenient defaults while retaining flexibility!
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

engine_type = 'online'
categories = ['general', 'web']
paging = False
language_support = True
time_range_support = True  # Supports from_time and to_time parameters
safesearch = False

# API configuration (will be overridden by settings.yml)
base_url = 'https://wsa.tencentcloudapi.com'
api_key = ''
secret_key = ''
mode = 0  # 0=Natural search (default), 1=Multimodal VR, 2=Mixed results
cnt = 10  # Number of results (10/20/30/40/50, Premium edition required for >10)
site = ''  # Domain-specific search
from_time = 0  # Start time (Unix timestamp in seconds), 0 means not set
to_time = 0  # End time (Unix timestamp in seconds), 0 means not set
industry = ''  # Industry filter: gov=Government, news=Media, acad=Academic (Premium only)


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
    date = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d')
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
    """Handle search request
    
    Supports both static configuration (from settings.yml) and dynamic parameters
    from search interface or query syntax.
    
    Dynamic parameter syntax:
    - Time: Use interface time range selector
    - Site: Use 'site:domain.com' in query, e.g., "!tc Python site:github.com"
    """

    # Get configuration from module-level variables (set by settings.yml)
    # These variables are set by SearXNG when loading the engine
    if not api_key or not secret_key:
        # If no API key configured, return empty results
        params['url'] = None
        return params

    # Parse dynamic site parameter from query
    # Support syntax: "keyword site:domain.com" or "site:domain.com keyword"
    dynamic_site = None
    clean_query = query
    
    # Check for site: syntax in query
    import re
    site_pattern = r'\bsite:(\S+)\b'
    site_match = re.search(site_pattern, query, re.IGNORECASE)
    if site_match:
        dynamic_site = site_match.group(1)
        # Remove site: part from query
        clean_query = re.sub(site_pattern, '', query, flags=re.IGNORECASE).strip()
    
    # Prepare request parameters
    timestamp = int(time.time())
    host = 'wsa.tencentcloudapi.com'

    # Build request body with cleaned query
    request_body = {'Query': clean_query, 'Mode': mode}

    # Add optional parameters
    # Cnt: Number of results (10/20/30/40/50, Premium edition required for >10)
    if cnt and cnt > 10:
        request_body['Cnt'] = cnt

    # Site: Domain-specific search (filters natural search results)
    # Supports three methods (priority from high to low):
    # 1. site: syntax in query (dynamic, highest priority)
    # 2. URL parameter passing (dynamic)
    # 3. Configuration file setting (static)
    # Note: Invalid in mode=1; effective in mode=0/2
    final_site = None
    
    if dynamic_site:
        # Use site: syntax from query first
        final_site = dynamic_site
    elif params.get('engine_data', {}).get('tencent', {}).get('site'):
        # Then use URL parameter
        final_site = params['engine_data']['tencent']['site']
    elif site:
        # Finally use static setting from config file
        final_site = site
    
    if final_site:
        request_body['Site'] = final_site

    # FromTime & ToTime: Time filtering (filters natural search results)
    # Supports two methods:
    # 1. Static settings from config file: from_time/to_time
    # 2. Dynamic selection from user interface: time_range (higher priority)
    if params.get('time_range'):
        # User selected time range in search interface, convert to timestamp
        range_map = {
            'day': 86400,      # 1 day in seconds
            'week': 604800,    # 7 days
            'month': 2592000,  # 30 days
            'year': 31536000   # 365 days
        }
        if params['time_range'] in range_map:
            # Calculate start time (current time - time range)
            request_body['FromTime'] = timestamp - range_map[params['time_range']]
            request_body['ToTime'] = timestamp
    else:
        # Use static time range from config file
        # FromTime: Start time (filters natural search results), precise to seconds
        # Note: Invalid in mode=1; effective in mode=0/2
        if from_time and from_time > 0:
            request_body['FromTime'] = int(from_time)

        # ToTime: End time (filters natural search results), precise to seconds
        # Note: Invalid in mode=1; effective in mode=0/2
        if to_time and to_time > 0:
            request_body['ToTime'] = int(to_time)

    # Industry: Industry filter (Premium edition only)
    # gov=Government agencies, news=Authoritative media, acad=Academic
    if industry and industry in ['gov', 'news', 'acad']:
        request_body['Industry'] = industry

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

                # Add optional fields - parse date string to datetime object
                if 'date' in page and page['date']:
                    # Try to parse the date string
                    # Common formats: "2024-01-15", "2024-01-15 10:30:00", etc.
                    date_str = page['date']
                    try:
                        # Try common date formats
                        for date_format in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d', '%Y-%m-%dT%H:%M:%S']:
                            try:
                                result['publishedDate'] = datetime.strptime(date_str, date_format)
                                break
                            except ValueError:
                                continue
                    except Exception:  # pylint: disable=broad-except
                        # If parsing fails, skip the date field
                        pass

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
