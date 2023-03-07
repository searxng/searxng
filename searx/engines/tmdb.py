from json import loads
import urllib.parse
SEARCH_URL = "https://api.themoviedb.org/3/search/multi"
API_KEY = "f6bd687ffa63cd282b6ff2c6877f2669"

def request(query, params):
    params["url"] = SEARCH_URL + "?api_key=" + API_KEY + "&query=" + urllib.parse.quote(query)
    language = params.get("language")
    if language:
        params["url"] += "&language=" + language
    pageno = params.get("pageno")
    if pageno:
        params["url"] += "&page=" + str(pageno)
    return params

def response(resp):
    results = []
    data = loads(resp.text)["results"]
    if data:
        for item in data:
            result = {
                "title": item.get("name"),
                "url": f"https://www.themoviedb.org/{item.get('media_type')}/{item.get('id')}",
                "content": item.get("overview"),
                "publishedDate": item.get("release_date") or item.get("first_air_date"),
            }
            results.append(result)
    return results