# SPDX-License-Identifier: AGPL-3.0-or-later
"""Plugin which reranks the search results using the Okapi BM25 algorithm.
Before enabling the Rerank plugin, you must the install the pip package ``bm25s``.

Enable in ``settings.yml``:

.. code:: yaml

  enabled_plugins:
    ..
    - 'Rerank plugin'

By default, the engine list is retained, so results found by multiple engines receive a score boost.
The following setting can be used to ensure that the engine list only contains the first engine.
This will prevent overlapping search engine results from affecting the ranking:

.. code:: yaml

  rerank:
    remove_extra_engines: true

"""

from searx import settings

try:
    import bm25s
except ImportError:
    # Import error is ignored because the admin has to install bm25s manually to use the engine
    pass

name = 'Rerank plugin'
description = 'Rerank search results, ignoring original engine ranking'
default_on = False
preference_section = 'general'

# Supported stopwords for bm25s. Default is 'en'
stopword_langs = ['en', 'de', 'nl', 'fr', 'es', 'pt', 'it', 'ru', 'sv', 'no', 'zh']

remove_extra_engines = settings.get('rerank', {}).get('remove_extra_engines')


def post_search(_request, search):
    # pylint: disable=protected-access
    results = search.result_container._merged_results
    query = search.search_query.query
    locale = search.search_query.locale

    # Determine the stopwords based on the selected locale
    stopwords = locale.language if locale and locale.language in stopword_langs else True

    retriever = bm25s.BM25()
    result_tokens = bm25s.tokenize(
        [f"{result.get('title', '')} | {result.get('content', '')} | {result.get('url', '')}" for result in results],
        stopwords=stopwords,
    )
    retriever.index(result_tokens)

    query_tokens = bm25s.tokenize(query, stopwords=stopwords)

    # Retrieve ranked indices of results based on the query tokens
    indices = retriever.retrieve(query_tokens, k=len(results), return_as='documents', show_progress=False)

    if remove_extra_engines:
        # Only keep the main engine and set our ranking
        for position, index in enumerate(indices[0]):
            if 'positions' in results[index]:
                results[index]['positions'] = [position + 1]
                results[index]['engines'] = set([results[index]['engine']])
    else:
        # Overwrite all engine positions with the new ranking
        # Results returned from multiple engines will still get a score boost
        for position, index in enumerate(indices[0]):
            if 'positions' in results[index]:
                results[index]['positions'] = [position + 1] * len(results[index]['positions'])

    return True
