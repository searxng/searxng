# SPDX-License-Identifier: AGPL-3.0-or-later
"""AI Enhancement Plugin

This plugin enhances search results with AI-powered features:
- Relevance scoring for each result
- Result summaries
- Query refinement suggestions

Supported AI backends:
- Ollama (local, privacy-friendly)
- Anthropic Claude
- OpenAI GPT

Configuration in settings.yml:
  plugins:
    - ai_enhancer:
        enabled: true
        backend: 'ollama'  # 'ollama', 'anthropic', 'openai'
        api_url: 'http://localhost:11434'  # for Ollama
        api_key: ''  # for Anthropic/OpenAI
        model: 'llama2'  # model to use
        max_results_to_analyze: 5
        enable_summaries: true
        enable_scoring: true
"""

import typing
import json
from typing import Optional, Dict, Any, List

from flask_babel import gettext
from searx.result_types import EngineResults
from searx.plugins import Plugin, PluginInfo

if typing.TYPE_CHECKING:
    from searx.search import SearchWithPlugins
    from searx.extended_types import SXNG_Request
    from searx.plugins import PluginCfg


class SXNGPlugin(Plugin):
    """AI Enhancement Plugin for scoring and summarizing search results."""

    id = "ai_enhancer"

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__(plg_cfg)

        self.info = PluginInfo(
            id=self.id,
            name=gettext("AI Result Enhancer"),
            description=gettext("Enhance search results with AI-powered scoring and summaries"),
            preference_section="general",
        )

        # Configuration
        self.backend = plg_cfg.get('backend', 'ollama')
        self.api_url = plg_cfg.get('api_url', 'http://localhost:11434')
        self.api_key = plg_cfg.get('api_key', '')
        self.model = plg_cfg.get('model', 'llama2')
        self.max_results = plg_cfg.get('max_results_to_analyze', 5)
        self.enable_summaries = plg_cfg.get('enable_summaries', True)
        self.enable_scoring = plg_cfg.get('enable_scoring', True)

    def _call_ollama(self, prompt: str) -> Optional[str]:
        """Call Ollama API for text generation."""
        try:
            import httpx

            response = httpx.post(
                f"{self.api_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=10.0
            )

            if response.status_code == 200:
                return response.json().get('response', '')
        except Exception as e:
            self.log.debug(f"Ollama API error: {e}")

        return None

    def _call_anthropic(self, prompt: str) -> Optional[str]:
        """Call Anthropic Claude API."""
        try:
            import httpx

            response = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": self.model or "claude-3-haiku-20240307",
                    "max_tokens": 200,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                },
                timeout=10.0
            )

            if response.status_code == 200:
                content = response.json().get('content', [])
                if content and len(content) > 0:
                    return content[0].get('text', '')
        except Exception as e:
            self.log.debug(f"Anthropic API error: {e}")

        return None

    def _call_openai(self, prompt: str) -> Optional[str]:
        """Call OpenAI GPT API."""
        try:
            import httpx

            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model or "gpt-3.5-turbo",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 200,
                    "temperature": 0.3
                },
                timeout=10.0
            )

            if response.status_code == 200:
                choices = response.json().get('choices', [])
                if choices and len(choices) > 0:
                    return choices[0].get('message', {}).get('content', '')
        except Exception as e:
            self.log.debug(f"OpenAI API error: {e}")

        return None

    def _call_ai(self, prompt: str) -> Optional[str]:
        """Call configured AI backend."""
        if self.backend == 'ollama':
            return self._call_ollama(prompt)
        elif self.backend == 'anthropic':
            return self._call_anthropic(prompt)
        elif self.backend == 'openai':
            return self._call_openai(prompt)
        return None

    def _score_result(self, query: str, title: str, content: str) -> str:
        """Score a search result's relevance to the query."""
        prompt = f"""Rate the relevance of this search result to the query on a scale of high/medium/low.
Query: {query}
Title: {title}
Content: {content[:200]}

Respond with only one word: high, medium, or low."""

        response = self._call_ai(prompt)
        if response:
            response = response.strip().lower()
            if 'high' in response:
                return 'high'
            elif 'medium' in response:
                return 'medium'
            elif 'low' in response:
                return 'low'

        return 'medium'  # default

    def _summarize_result(self, title: str, content: str) -> Optional[str]:
        """Generate a brief summary of the result."""
        prompt = f"""Summarize this search result in one concise sentence (max 20 words):
Title: {title}
Content: {content[:300]}

Summary:"""

        return self._call_ai(prompt)

    def on_result(self, request: "SXNG_Request", search: "SearchWithPlugins", result: dict) -> bool:
        """Process each result and add AI enhancements."""

        # Only process first page and first N results for performance
        if search.search_query.pageno > 1:
            return True

        # Get result index
        result_idx = len([r for r in search.result_container.get_ordered_results() if r.get('url')])
        if result_idx >= self.max_results:
            return True

        query = search.search_query.query
        title = result.get('title', '')
        content = result.get('content', '')

        # Skip if no content to analyze
        if not title and not content:
            return True

        # Add AI scoring
        if self.enable_scoring:
            score = self._score_result(query, title, content)
            result['ai_score'] = score

        # Add AI summary
        if self.enable_summaries and content:
            summary = self._summarize_result(title, content)
            if summary:
                result['ai_summary'] = summary.strip()

        return True
