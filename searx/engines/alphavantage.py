# SPDX-License-Identifier: AGPL-3.0-or-later
"""Alpha Vantage (Stock Search)

This engine uses the Alpha Vantage SYMBOL_SEARCH endpoint to search for stock
symbols and company information. It handles the special field name format used
by Alpha Vantage API ("1. symbol", "2. name", etc.).
"""

# 引擎元数据
about = {
    "website": "https://www.alphavantage.co/",
    "wikidata_id": "Q",
    "official_api_documentation": "https://www.alphavantage.co/documentation/",
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
}

# 引擎配置
categories = ["finance"]
paging = False
language_support = False

# API 配置（将从 settings.yml 中读取）
base_url = "https://www.alphavantage.co/query"


# 搜索函数
def request(query, params):
    """构建搜索请求"""
    # 从 engine settings 获取 API key
    api_key = params['engine_settings'].get('api_key', '')
    if not api_key:
        # 如果没有 API key，返回空结果
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
    """解析响应并返回结果"""
    results = []

    try:
        json_data = resp.json()

        # 检查是否有错误
        if "Error Message" in json_data:
            return results

        if "Note" in json_data:
            # API 限额达到
            return results

        # 获取搜索结果
        best_matches = json_data.get("bestMatches", [])

        for match in best_matches:
            # 提取字段（处理特殊字段名）
            symbol = match.get("1. symbol", "")
            name = match.get("2. name", "")
            stock_type = match.get("3. type", "")
            region = match.get("4. region", "")
            currency = match.get("8. currency", "")
            match_score = match.get("9. matchScore", "0")

            # 构建结果
            result = {
                "title": f"{symbol} - {name}",
                "content": f"{stock_type} | {region} | {currency}",
                "url": f"https://finance.yahoo.com/quote/{symbol}",
                # 额外信息
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

    # 发送请求
    api_response = requests.get(test_params["url"], params=test_params["data"], timeout=10)

    # 解析结果
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
