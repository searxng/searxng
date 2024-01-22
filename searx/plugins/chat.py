from searx.search import SearchWithPlugins
from pathlib import Path
from gpt4all import GPT4All


name = "Chat Plugin"
description = "Similar to bing GPT or google bard in their respective searches"
default_on = False
preference_section = 'general'

def post_search(request, search: SearchWithPlugins) -> None:
    """Called after the search is done."""
    search_request = search.search_query
    container = search.result_container
    # container.infoboxes.append(container.infoboxes[0])
    container.chat_box = {'chat_box': 'GPT4All'}
    container.chat_box['content'] = 'Generating response to query: ' + f'\n{search_request.query}'

def generate_chat_content(query):
    model = GPT4All(model_name='gpt4all-falcon-q4_0.gguf',
            model_path=(Path.cwd() / 'searx' / 'plugins'),
            allow_download=False)

    system_template = """
    ### System Instructions: 
    1. Provide concise and directly relevant answers to the specific query in HTML format, emulating the style of an info box on a search engine.
    2. Only use appropriate HTML tags (e.g., `<div>`, `<p>`, `<h1>`) to structure the response. Do not use markdown syntax or backticks(```) to format the response.
    3. Directly address the query. For example, if the query is about a specific function or method in a programming language, focus on explaining and providing examples of that function or method.
    4. Include practical examples or code snippets relevant to the query.
    5. Keep definitions or explanations brief and specific, focusing only on aspects directly related to the query.
    """

    prompt_template = """
    ### Query: 
    {0}

    ### Expected Information Box:
    """
    with model.chat_session(system_template, prompt_template):
        response = model.generate(query, max_tokens=500, repeat_penalty=1.3)
        return str(response)
