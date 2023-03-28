import os
from flask import Flask, jsonify, request
import openai

app = Flask(__name__)

# retrieve ChatGPT API key from system variable
API_KEY = os.environ.get("CHATGPT_API_KEY")

# initialize OpenAI API client
openai.api_key = API_KEY
engine_id = "text-davinci-002"

@app.route('/chatgpt', methods=['GET'])
def chatgpt():
    query = request.args.get('query')
    response = openai.Completion.create(
        engine=engine_id,
        prompt=query,
        max_tokens=150,
        n=1,
        stop="\n"
    )
    chatgpt_response = response.choices[0].text
    return chatgpt_response

if __name__ == '__main__':
    app.run()
