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
       mode: 0  # 0-natural, 1-multimodal VR, 2-mixed
       disabled: false
       timeout: 5.0
       weight: 1.2

Advanced Configurations
-----------------------

**Multiple Search Modes:**

.. code:: yaml

   # Natural search (default)
   - name: tencent
     engine: tencent_engine
     shortcut: tc
     mode: 0

   # Multimodal VR search
   - name: tencent_vr
     engine: tencent_engine
     shortcut: tcvr
     mode: 1

   # Mixed results
   - name: tencent_mixed
     engine: tencent_engine
     shortcut: tcmix
     mode: 2
     cnt: 30  # Premium only

**Site-Specific Search:**

.. code:: yaml

   - name: tencent_zhihu
     engine: tencent_engine
     shortcut: tczh
     site: 'zhihu.com'

**Time Range Filtering:**

.. code:: yaml

   - name: tencent_recent
     engine: tencent_engine
     shortcut: tcrecent
     from_time: '2024-01-01 00:00:00'  # Optional: Start time
     to_time: '2024-12-31 23:59:59'    # Optional: End time

**Industry Filtering (Premium):**

.. code:: yaml

   # News from authoritative media
   - name: tencent_news
     engine: tencent_engine
     shortcut: tcnews
     industry: 'news'
     categories: [news]

   # Academic resources
   - name: tencent_acad
     engine: tencent_engine
     shortcut: tcacad
     industry: 'acad'
     categories: [science]

   # Government sites
   - name: tencent_gov
     engine: tencent_engine
     shortcut: tcgov
     industry: 'gov'

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
site          string  Domain filter (e.g., 'zhihu.com')
from_time     string  Start time in 'YYYY-MM-DD HH:MM:SS' format
to_time       string  End time in 'YYYY-MM-DD HH:MM:SS' format
industry      string  Industry filter: 'news', 'acad', 'gov' (premium only)
timeout       float   Request timeout in seconds (default: 5.0)
weight        float   Result ranking weight (default: 1.0)
============= ======= ========================================================

**Note:** The ``from_time`` and ``to_time`` parameters can be used independently or together to filter results by publication date.

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
- ``!tcnews 科技新闻`` - Authoritative news (premium)

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

**UnauthorizedOperation:**

- Confirm Web Search API service is enabled
- Visit: https://console.cloud.tencent.com/wsa

**RequestLimitExceeded:**

- Check QPS limit (5 for basic, 20 for premium)
- Monitor daily quota usage
- Consider enabling caching
- Upgrade to premium tier if needed

**No Results:**

- Try different search mode (0/1/2)
- Check if query is filtered
- Verify API quota not exhausted
- Review logs for error messages

Performance Optimization
========================

1. **Enable Caching:**

   .. code:: yaml

      search:
        default_http_headers:
          Cache-Control: 'public, max-age=600'

2. **Adjust Timeout:**

   .. code:: yaml

      engines:
        - name: tencent
          timeout: 3.0  # Faster response

3. **Set Weight:**

   .. code:: yaml

      engines:
        - name: tencent
          weight: 1.5  # Higher priority for Chinese queries

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

Configuration Examples
======================

Complete configuration file available at:
``utils/tencent_settings_example.yml``

