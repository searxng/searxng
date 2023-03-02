import requests, os, json
gpt = ""
prompt = "你好"
gpt_url = "https://api.openai.com/v1/chat/completions"
gpt_headers = {
    "Authorization": "Bearer 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",
    "Content-Type": "application/json",    
}
gpt_data = {
    "model": "gpt-3.5-turbo",
    "messages": [{"role":"user","content":prompt}],
    "max_tokens": 256,
    "temperature": 0.9,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stream": False
    
}
gpt_response = requests.post(gpt_url, headers=gpt_headers, data=json.dumps(gpt_data))
if prompt and prompt !='' :
    gpt_response = requests.post(gpt_url, headers=gpt_headers, data=json.dumps(gpt_data))
    gpt_json = gpt_response.json()
print(gpt_json)