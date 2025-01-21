.. _kagi engine:

Kagi
====

The Kagi engine scrapes search results from Kagi's HTML search interface.

Example
-------

Configuration
~~~~~~~~~~~~

.. code:: yaml

   - name: kagi
     engine: kagi
     shortcut: kg
     categories: [general, web]
     timeout: 4.0
     api_key: "YOUR-KAGI-TOKEN"  # required
     about:
       website: https://kagi.com
       use_official_api: false
       require_api_key: true
       results: HTML


Parameters
~~~~~~~~~~

``api_key`` : required
  The Kagi API token used for authentication. Can be obtained from your Kagi account settings.

``pageno`` : optional
  The page number for paginated results. Defaults to 1.

Example Request
~~~~~~~~~~~~~~

.. code:: python

   params = {
       'api_key': 'YOUR-KAGI-TOKEN',
       'pageno': 1,
       'headers': {
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
           'Accept-Language': 'en-US,en;q=0.5',
           'DNT': '1'
       }
   }
   query = 'test query'
   request_params = kagi.request(query, params)

Example Response
~~~~~~~~~~~~~~

.. code:: python

   [
       # Search result
       {
           'url': 'https://example.com/',
           'title': 'Example Title',
           'content': 'Example content snippet...',
           'domain': 'example.com'
       }
   ]

Implementation
-------------

The engine performs the following steps:

1. Constructs a GET request to ``https://kagi.com/html/search`` with:
 - ``q`` parameter for the search query
 - ``token`` parameter for authentication
 - ``batch`` parameter for pagination

2. Parses the HTML response using XPath to extract:
 - Result titles
 - URLs
 - Content snippets
 - Domain information

3. Handles various error cases:
 - 401: Invalid API token
 - 429: Rate limit exceeded
 - Other non-200 status codes

Dependencies
-----------

- lxml: For HTML parsing and XPath evaluation
- urllib.parse: For URL handling and encoding
- searx.utils: For text extraction and XPath helpers

Notes
-----

- The engine requires a valid Kagi API token to function
- Results are scraped from Kagi's HTML interface rather than using an official API
- Rate limiting may apply based on your Kagi subscription level
- The engine sets specific browser-like headers to ensure reliable scraping
