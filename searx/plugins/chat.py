from searx.search import SearchWithPlugins


name = "Chat Plugin"
description = "Similar to bing GPT or google bard in their respective searches"
default_on = False
preference_section = 'general'

def post_search(request, search: SearchWithPlugins) -> None:
    """Called after the search is done."""
    search_request = search.search_query
    container = search.result_container
    # container.infoboxes.append(container.infoboxes[0])
    container.chat_box = container.infoboxes
    print(search_request)
    
    print("HELLO WORLD =====================================================================")