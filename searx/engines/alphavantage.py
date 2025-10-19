# SPDX-License-Identifier: AGPL-3.0-or-later
"""Alpha Vantage (Stock Search)

This engine uses the Alpha Vantage SYMBOL_SEARCH endpoint to search for stock
symbols and company information. It handles the special field name format used
by Alpha Vantage API ("1. symbol", "2. name", etc.).
"""

# Engine metadata
about = {
    "website": "https://www.alphavantage.co/",
    "wikidata_id": "Q",
    "official_api_documentation": "https://www.alphavantage.co/documentation/",
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
}

# Engine configuration
categories = ["finance"]
paging = False
language_support = False

# API configuration (read from settings.yml)
base_url = "https://www.alphavantage.co/query"


def request(query, params):
    """Build search request"""
    # Get API key from engine settings
    api_key = params['engine_settings'].get('api_key', '')
    if not api_key:
        # If no API key, return empty results
        params['url'] = None
        return params

    params["url"] = base_url
    params["method"] = "GET"
    params["data"] = {
        "function": "SYMBOL_SEARCH",
        "keywords": query,
        "apikey": api_key,
    }
    return params


def response(resp):
    """Parse response and return results"""
    results = []

    try:
        json_data = resp.json()

        # Check for errors
        if "Error Message" in json_data:
            return results

        if "Note" in json_data:
            # API rate limit reached
            return results

        # Get search results
        best_matches = json_data.get("bestMatches", [])

        for match in best_matches:
            # Extract fields (handle special field names)
            symbol = match.get("1. symbol", "")
            name = match.get("2. name", "")
            stock_type = match.get("3. type", "")
            region = match.get("4. region", "")
            currency = match.get("8. currency", "")
            match_score = match.get("9. matchScore", "0")

            # Build result
            result = {
                "title": f"{symbol} - {name}",
                "content": f"{stock_type} | {region} | {currency}",
                "url": f"https://finance.yahoo.com/quote/{symbol}",
                "metadata": f"Match Score: {float(match_score)*100:.0f}%",
            }

            results.append(result)

    except Exception:  # pylint: disable=broad-except
        # API parsing error, return empty results
        pass

    return results


# Manual testing
if __name__ == "__main__":
    import requests  # pylint: disable=import-outside-toplevel

    test_query = "AAPL"
    test_params = {
        "url": None,
        "method": "GET",
        "data": {},
        "engine_settings": {'api_key': 'EEPMIUJSP2LALKTM'},
    }

    test_params = request(test_query, test_params)

    print(f"Testing Alpha Vantage engine with query: {test_query}")
    print(f"URL: {test_params['url']}")
    print(f"Params: {test_params['data']}")

    # Send request
    api_response = requests.get(test_params["url"], params=test_params["data"], timeout=10)

    # Parse results
    class MockResponse:  # pylint: disable=too-few-public-methods
        """Mock response for testing"""

        def __init__(self, data):
            self._data = data

        def json(self):
            return self._data

    test_results = response(MockResponse(api_response.json()))

    print(f"\nFound {len(test_results)} results:")
    for idx, item in enumerate(test_results[:3], 1):
        print(f"\n{idx}. {item['title']}")
        print(f"   {item['content']}")
        print(f"   URL: {item['url']}")
        print(f"   {item['metadata']}")
