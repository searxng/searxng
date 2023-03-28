from searxng.utils import searxng_useragent
import requests

# Engine configuration
engine_type = 'online_dictionary'
categories = ['general']
paging = False
language_support = False

# ChatGPT API settings
base_url = 'https://api.openai.com/v1/engines/davinci-codex/completions'
chatgpt_api_key_var = 'chatgpt_api_key_var'
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {chatgpt_api_key_var}'
}

# Search function
def request(query, params):
    prompt = f"Search results summary for the query: {query}"
    data = {
        'prompt': prompt,
        'max_tokens': 60,
        'n': 1,
        'stop': None,
        'temperature': 0.5
    }

    response = requests.post(base_url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def response(resp):
    results = []
    chatgpt_response = resp['choices'][0]['text']
    results.append({'title': 'ChatGPT Summary', 'content': chatgpt_response.strip()})
    return results
