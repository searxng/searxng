import os
import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")
engine_id = "text-davinci-002"

def generate_response(prompt):
    response = openai.Completion.create(
        engine=engine_id,
        prompt=prompt,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7
    )
    return response.choices[0].text.strip()
