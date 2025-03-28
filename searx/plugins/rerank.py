# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring, missing-class-docstring
from __future__ import annotations
import typing

from flask_babel import gettext

from searx import settings
from searx.plugins import Plugin, PluginInfo
from searx.result_types import EngineResults

if typing.TYPE_CHECKING:
    from searx.search import SearchWithPlugins
    from searx.extended_types import SXNG_Request

try:
    import bm25s
except ImportError:
    # Import error is ignored because the admin has to install bm25s manually to use the plugin
    bm25s = None


class SXNGPlugin(Plugin):
    """Plugin which reranks the search results using the Okapi BM25 algorithm.

    This plugin utilizes the `bm25s` library to reorder search results based on their relevance to the search query,
    potentially improving the quality of results.  Before enabling this plugin,
    ensure you have installed the ``bm25s`` pip package.  e.g. by installing it directly via pip or
    by adding it to the project's `requirements.txt` file.

    Configuration:
    --------------
    To enable the Rerank plugin, add it to the `enabled_plugins` list in your `settings.yml` file:

    .. code:: yaml

    enabled_plugins:
        ..
        - 'Rerank plugin'

    By default, the plugin retains the information about which engines found a particular result.
    Results that appear in multiple engine results will receive a score boost.
    This approach might be relevant if you wish results found by different engines to be prioritized.
    You can modify this behaviour by configuring the ``remove_extra_engines`` setting.
    If ``remove_extra_engines`` is set to ``true``, the original engine list is reduced to only the first engine.
    This is useful when you prefer the reranking to not be affected by any potential overlap
    of results from different engines.

    .. code:: yaml

    rerank:
        remove_extra_engines: true

    """

    id = "rerank"
    default_on = False

    def __init__(self):
        super().__init__()

        self.stopword_langs = ['en', 'de', 'nl', 'fr', 'es', 'pt', 'it', 'ru', 'sv', 'no', 'zh']
        self.remove_extra_engines = settings.get('rerank', {}).get('remove_extra_engines')

        self.info = PluginInfo(
            id=self.id,
            name=gettext("Rerank plugin"),
            description=gettext("""Rerank search results, ignoring original engine ranking"""),
            preference_section="general",
            is_allowed=bm25s is not None,
        )

    def post_search(self, request: "SXNG_Request", search: "SearchWithPlugins") -> EngineResults:
        results = EngineResults()

        if not bm25s:
            return results

        # pylint: disable=protected-access
        results = search.result_container._merged_results
        query = search.search_query.query
        locale = search.search_query.locale

        # Determine the stopwords based on the selected locale
        stopwords = locale.language if locale and locale.language in self.stopword_langs else 'en'

        retriever = bm25s.BM25()
        result_tokens = bm25s.tokenize(
            [
                f"{result.get('title', '')} | {result.get('content', '')} | {result.get('url', '')}"
                for result in results
            ],
            stopwords=stopwords,
        )
        retriever.index(result_tokens)

        query_tokens = bm25s.tokenize(query, stopwords=stopwords)

        # Retrieve ranked indices of results based on the query tokens
        indices = retriever.retrieve(query_tokens, k=len(results), return_as='documents', show_progress=False)

        if self.remove_extra_engines:
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

        return results
