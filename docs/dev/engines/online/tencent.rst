.. _tencent engine:

====================
Tencent Cloud Search
====================

Tencent Cloud Web Search API (腾讯云联网搜索API) provides high-quality web search
with excellent Chinese language support.

.. automodule:: searx.engines.tencent
   :members:

Features
========

✅ Optimized for Chinese search results  
✅ Multiple search modes (natural, multimodal VR, mixed)  
✅ Site-specific search filtering  
✅ Time range filtering  
✅ Industry filtering (premium tier)  
✅ Relevance scoring  
✅ Rich metadata (title, URL, summary, date, images)

Configuration
=============

Prerequisites
-------------

1. Register at https://cloud.tencent.com
2. Enable Web Search API: https://cloud.tencent.com/product/wsa
3. Get API credentials: https://console.cloud.tencent.com/cam/capi

Quota Limits:

========== === ========== ============ ==================
Tier       QPS Daily Quota Results      Special Features
========== === ========== ============ ==================
Basic      5   1,000      10           -
Premium    20  10,000     up to 50     Industry filtering
========== === ========== ============ ==================

Basic Configuration
-------------------

.. code:: yaml

   engines:
     - name: tencent
       engine: tencent
       shortcut: tc
       categories: [general, web]
       api_key: "YOUR_SECRET_ID"
       secret_key: "YOUR_SECRET_KEY"
       disabled: false
       timeout: 10.0  # Recommended 10-15 seconds
       weight: 1.2

.. note::
   All optional parameters (mode, cnt, site, from_time, to_time) can be configured in settings.yml
   or passed dynamically via URL parameters.

Advanced Configurations
-----------------------

**Multiple Search Modes:**

.. code:: yaml

   # Natural search (default)
   - name: tencent
     engine: tencent
     shortcut: tc
     mode: 0

   # Multimodal VR search
   - name: tencent-vr
     engine: tencent
     shortcut: tcvr
     mode: 1
     disabled: true

   # Mixed results
   - name: tencent-mixed
     engine: tencent
     shortcut: tcmix
     mode: 2
     cnt: 30  # Premium only
     timeout: 15.0  # Larger result count needs more time
     disabled: true

**Site-Specific Search:**

.. code:: yaml

   - name: tencent-zhihu
     engine: tencent
     shortcut: tczh
     site: 'zhihu.com'

   - name: tencent-xueqiu
     engine: tencent
     shortcut: tcxq
     site: 'xueqiu.com'

**Time Range Filtering:**

.. code:: yaml

   - name: tencent-recent
     engine: tencent
     shortcut: tcrecent
     from_time: 20240101     # YYYYMMDD format
     to_time: 20241231       # Or Unix timestamp: 1735689599

.. note::
   Time filtering behavior depends on search mode:
   
   - **mode=0** (natural): Time filter applies to all results
   - **mode=1** (VR): Time filter is ignored
   - **mode=2** (mixed): Time filter applies to natural results only

Configuration Parameters
========================

Required Parameters
-------------------

============= ======= ========================================================
Parameter     Type    Description
============= ======= ========================================================
api_key       string  Tencent Cloud SecretId
secret_key    string  Tencent Cloud SecretKey
============= ======= ========================================================

Optional Parameters
-------------------

============= ======= ========================================================
Parameter     Type    Description
============= ======= ========================================================
mode          integer Search mode: 0=natural (default), 1=multimodal VR, 2=mixed
cnt           integer Results count (10/20/30/40/50, premium tier for >10)
site          string  Domain filter (e.g., 'zhihu.com', 'xueqiu.com')
from_time     integer Start time: YYYYMMDD (e.g., 20180101) or Unix timestamp
to_time       integer End time: YYYYMMDD (e.g., 20181231) or Unix timestamp
timeout       float   Request timeout in seconds (default: 10.0, recommend 10-15)
weight        float   Result ranking weight (default: 1.0)
============= ======= ========================================================

**Time Format Details:**

- **YYYYMMDD format** (e.g., ``20180101``): Automatically converted to Unix timestamp

  - ``from_time``: Converted to 00:00:00 UTC of the specified date
  - ``to_time``: Converted to 23:59:59 UTC of the specified date

- **Unix timestamp** (e.g., ``1514764800``): Used directly (seconds since epoch)

**Notes:**

- Time parameters work with ``mode=0`` (all results) and ``mode=2`` (natural results only)
- Time parameters are ignored when ``mode=1`` (VR search)
- Can use ``from_time`` and ``to_time`` independently or together

Usage
=====

Search Examples
---------------

Basic search:

- ``!tc 北京天气`` - General search
- ``!tc 人工智能`` - Technology search
- ``!tcvr 风景图片`` - Multimodal VR search

Site-specific:

- ``!tczh Python教程`` - Search within Zhihu
- ``!tcxq 投资策略`` - Search within Xueqiu

Dynamic URL Parameters
----------------------

You can override settings.yml configuration by passing parameters in the URL. This is useful for:

- API integrations
- Dynamic filtering
- User-specific searches
- A/B testing

**URL Parameter Format:**

.. code::

   ?q=search_query&engine_data-tencent-<parameter>=<value>

**Available Parameters:**

================= ============ ==============================================
Parameter         Example      Description
================= ============ ==============================================
mode              2            Search mode (0/1/2)
cnt               50           Number of results (10-50)
site              xueqiu.com   Filter by domain
from_time         20180101     Start date (YYYYMMDD or Unix timestamp)
to_time           20181231     End date (YYYYMMDD or Unix timestamp)
================= ============ ==============================================

**Example URLs:**

Search with mixed mode and 50 results:

.. code::

   /search?q=人工智能&engine_data-tencent-mode=2&engine_data-tencent-cnt=50

Search within specific site:

.. code::

   /search?q=投资&engine_data-tencent-site=xueqiu.com

Search with time range (2018):

.. code::

   /search?q=市场分析&engine_data-tencent-from_time=20180101&engine_data-tencent-to_time=20181231

Combined parameters:

.. code::

   /search?q=科技&engine_data-tencent-mode=2&engine_data-tencent-cnt=50&engine_data-tencent-site=xueqiu.com&engine_data-tencent-from_time=20180101&engine_data-tencent-to_time=20181231

**Priority:** URL parameters > settings.yml > defaults

**Programmatic Usage:**

.. code:: python

   import requests
   
   # Python example
   response = requests.get('http://your-searxng/search', params={
       'q': '市场趋势',
       'engine_data-tencent-from_time': '20180101',
       'engine_data-tencent-to_time': '20181231',
       'format': 'json'
   })
   
   results = response.json()['results']

Testing
=======

Testing
-------

Run unit tests:

.. code:: bash

   # Run all unit tests (includes Tencent engine tests)
   make test.unit

Manual Testing
--------------

After deployment, test manually:

.. code:: bash

   # Test through SearXNG
   curl "http://localhost:8888/search?q=北京天气&format=json&engines=tencent"
   
   # Or use the custom engine test
   ./manage test.custom_engines http://localhost:8888

Direct API Test
---------------

To verify API credentials without deploying, you can test directly:

.. code:: bash

   # Using curl (replace with your credentials)
   curl -X POST https://wsa.tencentcloudapi.com/ \
     -H "Authorization: TC3-HMAC-SHA256 ..." \
     -H "Content-Type: application/json" \
     -H "X-TC-Action: SearchPro" \
     -d '{"Query":"测试","Mode":0}'

Expected response:

.. code:: json

   {
     "query": "北京天气",
     "results": [
       {
         "url": "https://...",
         "title": "北京天气预报",
         "content": "今天北京天气...",
         "publishedDate": "2025-10-18 10:00:00",
         "metadata": "中国天气网 (相关性: 0.95)",
         "engine": "tencent"
       }
     ]
   }

Troubleshooting
===============

Common Issues
-------------

**AuthFailure.SignatureFailure:**

- Verify SecretId and SecretKey are correct
- Check system time is synchronized
- Ensure no extra spaces in credentials
- Verify credentials have proper permissions

**UnauthorizedOperation:**

- Confirm Web Search API service is enabled
- Visit: https://console.cloud.tencent.com/wsa
- Check API key status (not expired/disabled)

**InvalidParameter - FromTime/ToTime type error:**

- Ensure time values are integers (not strings with quotes in YAML)
- Use YYYYMMDD format (e.g., ``20180101``) or Unix timestamp (e.g., ``1514764800``)
- Don't use ``'YYYY-MM-DD HH:MM:SS'`` format

**RequestLimitExceeded:**

- Check QPS limit (5 for basic, 20 for premium)
- Monitor daily quota usage
- Consider enabling caching
- Upgrade to premium tier if needed

**Engine Timeout:**

- Increase timeout value (``timeout: 15.0``)
- Reduce result count (``cnt: 10`` instead of ``cnt: 50``)
- Check network latency to Tencent Cloud
- Consider enabling connection pooling

**No Results:**

- Try different search mode (0/1/2)
- Check if query is filtered
- Verify API quota not exhausted
- Review logs for error messages
- Test with simple query first (e.g., "北京")

**Missing engine config attribute errors:**

- Don't define optional parameters as ``None`` in settings.yml
- Remove or comment out unused optional parameters
- See "Configuration Parameters" section for valid parameters

Performance Optimization
========================

1. **Optimize Timeout:**

   .. code:: yaml

      engines:
        - name: tencent
          timeout: 10.0  # Balance between speed and reliability
          cnt: 10        # Default count for faster response

   For large result counts, increase timeout:

   .. code:: yaml

      engines:
        - name: tencent-large
          cnt: 50
          timeout: 15.0

2. **Enable Caching:**

   .. code:: yaml

      search:
        default_http_headers:
          Cache-Control: 'public, max-age=600'

   Or use Redis/Valkey caching:

   .. code:: yaml

      valkey:
        url: redis://localhost:6379

3. **Set Weight for Chinese Queries:**

   .. code:: yaml

      engines:
        - name: tencent
          weight: 1.5  # Higher priority for Chinese content

4. **Connection Pooling:**

   SearXNG automatically handles connection pooling. For better performance:

   - Keep timeout reasonable (10-15 seconds)
   - Don't set ``cnt`` too high unless necessary
   - Monitor API quota usage

Security
========

**API Key Management:**

- Never commit credentials to version control
- Use environment variables or secrets management
- Rotate keys periodically
- Set IP whitelist in Tencent Cloud console

API Documentation
=================

- Product page: https://cloud.tencent.com/product/wsa
- API docs: https://cloud.tencent.com/document/product/1806/121811
- Signature v3: https://cloud.tencent.com/document/api/1806/121815
- Console: https://console.cloud.tencent.com/wsa
- Unit tests: ``tests/unit/engines/test_tencent.py``

Version History
===============

**v2.0** (2025-10)

- Fixed configuration parameter passing (URL params and settings.yml)
- Changed time format from string to Unix timestamp with YYYYMMDD support
- Added URL parameter support for dynamic configuration
- Improved timeout handling (default 10s)
- Fixed publishedDate parsing
- Added comprehensive unit tests

**v1.0** (2024)

- Initial release with basic search functionality

