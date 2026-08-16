# SPDX-License-Identifier: AGPL-3.0-or-later
"""Implementations needed for the AI Summary plugin
(:py:obj:`searx.plugins.ai_summary`)."""
# pylint: disable=too-few-public-methods

# Struct fields aren't discovered in Python 3.14
# - https://github.com/searxng/searxng/issues/5284
from __future__ import annotations

__all__ = ["SettingsAISummary", "MODELS", "model_choices", "build_chat_messages"]

import msgspec

DEFAULT_SYSTEM_PROMPT = (
    "You are a search assistant.  Answer the user's search query concisely in"
    " a few short paragraphs of plain text.  If you are unsure or don't know"
    " the answer, say so."
)

DEFAULT_SYSTEM_PROMPT_GROUNDED = (
    "You are a search assistant.  Answer the user's search query concisely in"
    " a few short paragraphs of plain text, using the following search results"
    " as context when they are relevant.  If you are unsure or don't know the"
    " answer, say so.\n\nSearch results:\n\n{context}"
)

MODELS: list[str] = []
"""List of model names a user can select from.  Populated once at
application setup by :py:obj:`searx.plugins.ai_summary.SXNGPlugin.init`."""


class SettingsAISummary(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    """Options for configuring the AI Summary plugin.

    .. code:: yaml

       ai_summary:
         base_url: "http://127.0.0.1:11434"
         model: "llama3.2:3b"
         models:
           - "llama3.2:3b"
           - "gemma3:4b"
    """

    base_url: str = ""
    """Default base URL of the LLM server (e.g. ``http://127.0.0.1:11434``
    for Ollama).  Any server that implements the OpenAI chat completions API
    works (Ollama, vLLM, llama.cpp, LM Studio, Hugging Face TGI, ...).  Users
    can set their own server URL in the preferences (``ai_summary_server``)
    unless that preference is locked."""

    api_key: str = ""
    """Optional API key of the LLM server in
    :py:obj:`SettingsAISummary.base_url`, sent in an ``Authorization: Bearer``
    header.  Needed by servers that require authentication, e.g. vLLM or
    llama.cpp started with ``--api-key``, or an LLM server behind an
    authenticating reverse proxy.

    This key is **only** sent to :py:obj:`SettingsAISummary.base_url`: a user
    who points the ``ai_summary_server`` preference at a server of their own
    gets no ``Authorization`` header from it, so the key can't be captured by
    a third party.  For their own server, users configure their own key in the
    ``ai_summary_api_key`` preference (see
    :py:obj:`searx.plugins.ai_summary._server_api_key`)."""

    model: str = ""
    """Name of the default model (e.g. ``llama3.2:3b``).  If empty, the first
    entry of :py:obj:`SettingsAISummary.models` is used.  Users can set their
    own model in the preferences (``ai_summary_model``) unless that preference
    is locked."""

    models: list[str] = []
    """List of model names suggested to the user in the preferences.  If empty
    and :py:obj:`SettingsAISummary.base_url` is set, the list is requested
    once at application setup from the LLM server (``GET /v1/models``)."""

    grounding: bool = True
    """Default of the ``ai_summary_grounding`` user preference: ground the
    summary on the search results.  Grounded summaries are more accurate and
    more current at a moderate extra cost (the search results are sent along
    with the query, so the prompt is longer).  Users can still opt in/out in
    the preferences unless that preference is locked."""

    connect_timeout: float = 5.0
    """Timeout (seconds) to establish a TCP connection to the LLM server."""

    read_timeout: float = 30.0
    """Maximum gap (seconds) between two chunks of the token stream."""

    stream_timeout: float = 120.0
    """Wall clock limit (seconds) for one completion."""

    max_context_items: int = 5
    """Maximum number of search results accepted as grounding context."""

    max_history_messages: int = 12
    """Maximum number of messages (follow-up chat history) per request."""

    max_message_length: int = 4000
    """Maximum length (characters) of a single message or context snippet."""

    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    """System prompt used when the *grounding* preference is off."""

    system_prompt_grounded: str = DEFAULT_SYSTEM_PROMPT_GROUNDED
    """System prompt used when the *grounding* preference is on.  The
    placeholder ``{context}`` is replaced by an enumeration of the search
    results sent along with the query."""


def model_choices() -> list[str]:
    """Model names a user can select from in the preferences."""
    return list(MODELS)


def build_chat_messages(
    cfg: SettingsAISummary,
    messages: list[dict[str, str]],
    context: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """Build the message list for the chat completions request from the
    (already validated) request ``messages``, prepending a system prompt.  When
    ``context`` items are given, the grounded system prompt is used and the
    context items are serialized into its ``{context}`` placeholder."""

    if context:
        ctx_lines = [
            f"[{no}] {item.get('title', '')} — {item.get('snippet', '')} ({item.get('url', '')})"
            for no, item in enumerate(context[: cfg.max_context_items], start=1)
        ]
        system_prompt = cfg.system_prompt_grounded.replace("{context}", "\n".join(ctx_lines))
    else:
        system_prompt = cfg.system_prompt

    return [{"role": "system", "content": system_prompt}, *messages]
