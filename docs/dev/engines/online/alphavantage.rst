.. _alphavantage engine:

=============
Alpha Vantage
=============

Alpha Vantage provides financial market data APIs. This engine uses the
SYMBOL_SEARCH endpoint to search for stock symbols and company information.

.. automodule:: searx.engines.alphavantage
   :members:

Configuration
=============

Prerequisites
-------------

1. Get a free API key from: https://www.alphavantage.co/support/#api-key
2. Free tier limits: 25 requests/day, 5 requests/minute

Basic Configuration
-------------------

Add the following to your ``settings.yml``:

.. code:: yaml

   engines:
     - name: alphavantage
       engine: alphavantage
       shortcut: av
       categories: [finance]
       api_key: "YOUR_API_KEY_HERE"
       disabled: false
       timeout: 5.0
       weight: 1.2

The ``api_key`` parameter is read from ``engine_settings`` at runtime, providing
better security than hardcoding in the engine file.

Usage
=====

Search Examples
---------------

- Stock symbols: ``!av AAPL``
- Company names: ``!av Microsoft``
- Ticker search: ``!av Tesla``

Results include:

- Stock symbol and company name
- Asset type (Equity, ETF, etc.)
- Region and currency
- Match score (0-1)

Testing
=======

Direct API Test
---------------

Test the API key before deployment:

.. code:: bash

   curl "https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords=AAPL&apikey=YOUR_KEY"

Engine Test
-----------

After deployment, run the unit tests:

.. code:: bash

   # Run unit tests
   make test.unit
   
   # Or test the engine manually
   curl "http://localhost:8888/search?q=AAPL&format=json&engines=alphavantage"
   
   # Or use the custom engine test
   ./manage test.custom_engines http://localhost:8888

Troubleshooting
===============

Common Issues
-------------

**No Results Returned:**

- Check API key validity
- Verify API quota not exceeded
- Ensure ``disabled: false`` in settings.yml

**API Rate Limit:**

Free tier is limited. Consider:

- Enabling result caching
- Reducing search frequency
- Upgrading to premium tier

API Documentation
=================

- Official docs: https://www.alphavantage.co/documentation/
- Symbol Search endpoint: https://www.alphavantage.co/documentation/#symbolsearch
- Support: https://www.alphavantage.co/support/

