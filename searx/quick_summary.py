# SPDX-License-Identifier: AGPL-3.0-or-later
"""Quick Summary module for LLM-powered search result summarization."""

import typing as t
import hashlib
import re
import httpx
import json

from searx import logger
from searx import get_setting
from searx.cache import ExpireCacheSQLite, ExpireCacheCfg

log = logger.getChild("quick_summary")

# Initialize cache
_cache_config = ExpireCacheCfg(
    name='quick_summary',
    MAXHOLD_TIME=60 * 60 * 24,  # 24 hours
)
_summary_cache = ExpireCacheSQLite(_cache_config)


def create_summary_prompt(query: str, results: list[dict]) -> str:
    """Create a prompt for the LLM with citation instructions."""
    
    results_text = "\n\n".join([
        f"Result {i+1}:\n"
        f"Title: {r.get('title', '')}\n"
        f"URL: {r.get('url', '')}\n"
        f"Content: {r.get('content', '')[:500]}"
        for i, r in enumerate(results)
    ])
    
    prompt = f"""You are a helpful search assistant. Summarize the search results for the query: "{query}"

Here are the top {len(results)} search results:

{results_text}

Instructions:
1. Provide a concise 3-5 paragraph summary
2. Use citations like [1], [2], [3] to reference specific results by their number
3. Each citation should correspond to the exact result number from the list above
4. Include key facts, insights, and consensus from the results
5. Highlight any disagreements or conflicting information with citations
6. Focus on accuracy and relevance to the original query
7. Only use information from the provided search results
8. Do not make up facts or include information not in the sources

Summary:"""

    return prompt


def parse_llm_response(response_text: str, results: list[dict]) -> dict:
    """Parse LLM response and extract citations.
    
    Returns:
        dict with keys: 'summary' (str), 'citations' (list), 'error' (None)
    """
    try:
        # Extract citation numbers from response
        citation_matches = re.findall(r'\[(\d+)\]', response_text)
        
        citations = []
        for match in citation_matches:
            citation_num = int(match)
            # Validate citation index
            if 1 <= citation_num <= len(results):
                result_idx = citation_num - 1
                if result_idx not in [c.get('result_index') for c in citations]:
                    # Find where in the text this citation appears
                    citation_text = extract_citation_text(response_text, citation_num)
                    citations.append({
                        'index': citation_num,
                        'text': citation_text,
                        'result_index': result_idx,
                        'title': results[result_idx].get('title', ''),
                        'url': results[result_idx].get('url', '')
                    })
        
        return {
            'summary': response_text,
            'citations': citations,
            'error': None
        }
    except Exception as e:
        log.error(f"Error parsing LLM response: {e}")
        return {
            'summary': response_text,
            'citations': [],
            'error': str(e)
        }


def extract_citation_text(text: str, citation_num: int) -> str:
    """Extract the text around a citation marker."""
    # Find the citation and get context (up to 50 chars)
    pattern = re.escape(f"[{citation_num}]")
    # Build regex pattern without f-string brace escaping
    regex_pattern = r'.{0,50}' + pattern + r'.{0,50}'
    match = re.search(regex_pattern, text)
    if match:
        return match.group().strip()
    return ""


def get_cache_key(query: str, max_results: int) -> str:
    """Generate a cache key for the summary request."""
    key_data = f"{query}:{max_results}"
    return hashlib.sha256(key_data.encode()).hexdigest()[:32]


async def call_openai_compatible_api(
    api_url: str,
    api_key: str,
    model: str,
    prompt: str,
    timeout: float = 30.0
) -> dict:
    """Call an OpenAI-compatible API asynchronously.
    
    Args:
        api_url: Base URL of the API (e.g., 'https://api.openai.com/v1')
        api_key: API key for authentication
        model: Model name to use
        prompt: The prompt to send
        timeout: Timeout in seconds
    
    Returns:
        dict with 'text' (str) or 'error' (str)
    """
    try:
        # Ensure URL has correct endpoint
        if not api_url.endswith('/chat/completions'):
            api_url = api_url.rstrip('/') + '/chat/completions'
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        
        payload = {
            'model': model,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.3,
            'max_tokens': 1000
        }
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                api_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different API response formats
            if 'choices' in data and len(data['choices']) > 0:
                text = data['choices'][0].get('message', {}).get('content', '')
                return {'text': text, 'error': None}
            elif 'output' in data:  # Some APIs use 'output' instead
                text = data['output'].get('text', '')
                return {'text': text, 'error': None}
            else:
                return {'text': '', 'error': 'Unexpected API response format'}
    
    except httpx.TimeoutException as e:
        log.error(f"LLM API timeout: {e}")
        return {'text': '', 'error': 'API request timed out. Please try again.'}
    except httpx.HTTPStatusError as e:
        log.error(f"LLM API HTTP error: {e.response.status_code}")
        if e.response.status_code == 401:
            return {'text': '', 'error': 'Invalid API key. Please check your credentials.'}
        elif e.response.status_code == 429:
            return {'text': '', 'error': 'Rate limit exceeded. Please try again later.'}
        elif e.response.status_code == 500:
            return {'text': '', 'error': 'API server error. Please try again.'}
        else:
            return {'text': '', 'error': f'API error: {e.response.status_code}'}
    except httpx.RequestError as e:
        log.error(f"LLM API request error: {e}")
        return {'text': '', 'error': 'Failed to connect to API. Please check your API URL.'}
    except json.JSONDecodeError as e:
        log.error(f"LLM API JSON decode error: {e}")
        return {'text': '', 'error': 'Invalid API response. Please try again.'}
    except Exception as e:
        log.exception(f"Unexpected LLM API error: {e}")
        return {'text': '', 'error': f'Unexpected error: {str(e)}'}


async def generate_summary(
    query: str,
    results: list[dict],
    api_config: dict,
    max_results: int,
    use_cache: bool = True
) -> dict:
    """Generate a summary of search results using LLM.
    
    Args:
        query: The search query
        results: List of search result dicts with 'title', 'url', 'content'
        api_config: Dict with 'api_base_url', 'api_key', 'model'
        max_results: Number of results to include in summary
        use_cache: Whether to check cache
    
    Returns:
        dict with keys:
            - 'summary': The generated summary text
            - 'citations': List of citation dicts
            - 'error': Error message if any, None otherwise
            - 'cached': Boolean indicating if from cache
    """
    # Validate inputs
    if not query:
        return {'summary': '', 'citations': [], 'error': 'No query provided', 'cached': False}
    
    if not results:
        return {'summary': '', 'citations': [], 'error': 'No results to summarize', 'cached': False}
    
    if not api_config.get('api_key'):
        return {'summary': '', 'citations': [], 'error': 'API key not configured', 'cached': False}
    
    # Limit results
    results = results[:max_results]
    
    # Check cache
    cache_key = get_cache_key(query, max_results)
    if use_cache:
        cached_result = _summary_cache.get(cache_key)
        if cached_result:
            log.info(f"Returning cached summary for query: {query[:50]}...")
            cached_result['cached'] = True
            return cached_result
    
    # Generate prompt
    prompt = create_summary_prompt(query, results)
    
    # Call LLM API
    api_url = api_config.get('api_base_url', '')
    api_key = api_config.get('api_key', '')
    model = api_config.get('model', 'gpt-4o-mini')
    
    api_response = await call_openai_compatible_api(api_url, api_key, model, prompt)
    
    if api_response.get('error'):
        return {
            'summary': '',
            'citations': [],
            'error': api_response['error'],
            'cached': False
        }
    
    # Parse response
    summary_text = api_response['text']
    parsed = parse_llm_response(summary_text, results)
    
    if parsed.get('error'):
        return {
            'summary': summary_text,
            'citations': parsed.get('citations', []),
            'error': parsed['error'],
            'cached': False
        }
    
    # Store in cache
    cache_data = {
        'summary': parsed['summary'],
        'citations': parsed['citations'],
        'error': None,
        'cached': False
    }
    _summary_cache.set(cache_key, cache_data, expire=86400)  # 24 hours
    
    log.info(f"Generated summary for query: {query[:50]}...")
    
    return cache_data
