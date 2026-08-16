# SPDX-License-Identifier: AGPL-3.0-or-later
"""Implementation of the AI Summary plugin, which shows a generated answer above
the search results.  The answer comes from an LLM server that implements the
`OpenAI chat completions API`_ (Ollama, vLLM, llama.cpp, LM Studio, Hugging Face
TGI, ...) and that the administrator runs.

- :ref:`ai_summary plugin` describes the design and the request flow.
- :ref:`settings ai_summary` describes how to configure it.

This module holds the plugin itself and the ``/ai_summary`` endpoint
(:py:obj:`ai_summary_view`, registered in :py:obj:`searx.webapp`).  The endpoint
streams the answer to the browser, so that the result page is never delayed by
the LLM; :py:obj:`SXNGPlugin.post_search` only adds an empty
:py:obj:`searx.result_types.AiSummary` placeholder for the client to fill.

Settings of the ``ai_summary:`` section are defined in
:py:obj:`searx.ai_summary.SettingsAISummary`.

.. _OpenAI chat completions API: https://platform.openai.com/docs/api-reference/chat
"""

import typing as t

import json
import logging
import re
import time
from urllib.parse import urlparse

import flask
import httpx
from flask_babel import gettext

from searx import get_setting
from searx.ai_summary import SettingsAISummary, build_chat_messages
from searx.extended_types import sxng_request
from searx.result_types import EngineResults
import searx.ai_summary

from . import Plugin, PluginInfo

if t.TYPE_CHECKING:
    from searx.search import SearchWithPlugins
    from searx.extended_types import SXNG_Request
    from . import PluginCfg

VALID_ROLES = ("user", "assistant")
# Model names differ per provider: "gemma3:4b" (Ollama), "bedrock/anthropic.
# claude-3-5-sonnet" (a gateway's routing prefix), "gemini-1.5-pro@001" (a
# pinned version).  The pattern accepts those and rejects anything that could
# change the meaning of the request body it is placed into.
MODEL_NAME_REGEXP = re.compile(r"[A-Za-z0-9._:/@-]{1,128}")

log = logging.getLogger("searx.plugins.ai_summary")

UPSTREAM_RETRIES = 1
"""How often a request to the LLM server is repeated when the server does not
answer in time.

An idle LLM server unloads the model, and loads it again on the next request --
which can take longer than :py:obj:`read_timeout
<searx.ai_summary.SettingsAISummary.read_timeout>`, because no byte of the
response is sent while the model is loading.  The request that runs into this
is also the request that starts the load, so repeating it usually succeeds."""


def _get_client(base_url: str, cfg: SettingsAISummary, api_key: str = "") -> httpx.Client:
    """HTTP client for one request to the LLM server at ``base_url``.  The
    ``api_key`` (if any) is sent in an ``Authorization: Bearer`` header, see
    :py:obj:`_server_api_key`."""
    # the OpenAI API paths are prefixed with /v1, unless the base URL already
    # points into an API prefix
    base_url = base_url.rstrip("/")
    if not base_url.endswith("/v1"):
        base_url += "/v1"
    return httpx.Client(
        base_url=base_url,
        headers={"Authorization": f"Bearer {api_key}"} if api_key else None,
        timeout=httpx.Timeout(connect=cfg.connect_timeout, read=cfg.read_timeout, write=10.0, pool=10.0),
    )


def _valid_server(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc) and len(url) <= 256


def _server_id(url: str) -> tuple[str, str, int, str] | None:
    """Identity of an LLM server URL (scheme, host, port, path) for comparing
    two URLs, or ``None`` if the URL is unusable.  The ``/v1`` API prefix is
    not part of the identity, :py:obj:`_get_client` appends it when missing."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    # .hostname (not .netloc) drops the userinfo, so that a server URL like
    # http://llm.example.org@untrusted.example.org/ is identified by the host
    # the request is actually sent to (untrusted.example.org)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return None
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = parsed.path.rstrip("/")
    if path.endswith("/v1"):
        path = path[: -len("/v1")].rstrip("/")
    return (parsed.scheme, parsed.hostname.lower(), port, path)


def _server_api_key(cfg: SettingsAISummary, server: str, user_api_key: str = "") -> str:
    """The API key to send to ``server``:

    - the administrator's :py:obj:`cfg.api_key
      <searx.ai_summary.SettingsAISummary.api_key>` if ``server`` *is* the
      administrator's server (:py:obj:`cfg.base_url
      <searx.ai_summary.SettingsAISummary.base_url>`),
    - otherwise the user's own ``ai_summary_api_key`` preference, which belongs
      to the server in the user's own ``ai_summary_server`` preference.

    The administrator's key is never sent to a server a user configured --
    that would hand every user of the instance a way to capture it."""
    server_id = _server_id(server)
    if server_id is not None and server_id == _server_id(cfg.base_url):
        return cfg.api_key
    return user_api_key


def _user_server(request: "SXNG_Request", cfg: SettingsAISummary) -> str:
    """The LLM server URL for this request: the user's ``ai_summary_server``
    preference, or the administrator's default."""
    server = str(request.preferences.get_value("ai_summary_server") or "").strip()
    # Credentials are stripped from a user's server URL: httpx turns them into
    # an Authorization header, and a user should not be able to make SearXNG
    # send a header of their choosing to a host of their choosing.  An
    # administrator can still use credentials in the configured base_url (e.g.
    # an LLM server behind basic auth).
    if server and "@" in urlparse(server).netloc:
        server = ""
    return server or cfg.base_url


class SXNGPlugin(Plugin):
    """Plugin that adds the AI summary placeholder to the result page, the
    ``/ai_summary`` endpoint itself is registered in :py:obj:`searx.webapp`."""

    id = "ai_summary"

    def __init__(self, plg_cfg: "PluginCfg"):
        super().__init__(plg_cfg)

        self.info = PluginInfo(
            id=self.id,
            name=gettext("AI Summary"),
            description=gettext(
                "Show an AI generated summary of the search query on top of the"
                " result page (uses a local LLM server, see the settings below)."
            ),
            preference_section="ai",
        )

    def init(self, app: "flask.Flask") -> bool:
        cfg: SettingsAISummary = get_setting("ai_summary")

        if cfg.base_url:
            searx.ai_summary.MODELS = list(cfg.models) or self._probe_models(cfg)
            if not cfg.model and searx.ai_summary.MODELS:
                cfg.model = searx.ai_summary.MODELS[0]
            if cfg.model and cfg.model not in searx.ai_summary.MODELS:
                searx.ai_summary.MODELS.insert(0, cfg.model)

        return True

    def _probe_models(self, cfg: SettingsAISummary) -> list[str]:
        """Request the list of models from the LLM server (``GET
        /v1/models``).  The server might not be up when SearXNG starts, a
        failing probe only leaves the model suggestion list empty."""
        try:
            with _get_client(cfg.base_url, cfg, cfg.api_key) as client:
                resp = client.get("/models")
                resp.raise_for_status()
                models = [model["id"] for model in resp.json().get("data", [])]
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            self.log.warning("can't request model list from %s: %s", cfg.base_url, exc)
            models = []
        return models or ([cfg.model] if cfg.model else [])

    def post_search(self, request: "SXNG_Request", search: "SearchWithPlugins") -> EngineResults | None:
        results = EngineResults()
        sq = search.search_query
        cfg: SettingsAISummary = get_setting("ai_summary")

        skip = (
            sq.pageno > 1
            # post_search is also called for the json, csv and rss formats,
            # the placeholder is only useful on the HTML result page
            or request.form.get("format", "html") != "html"
            or "general" not in sq.categories
            # an infobox (e.g. wikipedia / wikidata) or an instant answer
            # (e.g. ddg definitions) most likely already answers the query
            or bool(search.result_container.infoboxes)
            or bool(search.result_container.answers)
            or not sq.query.strip()
            # without an LLM server (user preference or admin default)
            # there is nothing to show
            or not _user_server(request, cfg)
        )
        if skip:
            return None

        grounding = bool(request.preferences.get_value("ai_summary_grounding"))
        results.add(results.types.AiSummary(query=sq.query, grounding=grounding))
        return results


def _bad_request(msg: str) -> flask.Response:
    return flask.Response(json.dumps({"error": msg}), status=400, mimetype="application/json")


def _validate_messages(messages: t.Any, cfg: SettingsAISummary) -> list[dict[str, str]]:
    if not isinstance(messages, list) or not messages or len(messages) > cfg.max_history_messages:
        raise ValueError("invalid messages")
    for msg in messages:
        if not isinstance(msg, dict) or msg.keys() != {"role", "content"}:
            raise ValueError("invalid message")
        if msg["role"] not in VALID_ROLES or not isinstance(msg["content"], str):
            raise ValueError("invalid message")
        if not msg["content"].strip() or len(msg["content"]) > cfg.max_message_length:
            raise ValueError("invalid message")
    if messages[-1]["role"] != "user":
        raise ValueError("last message is not a user message")
    return messages


def _validate_context(context: t.Any, cfg: SettingsAISummary) -> list[dict[str, str]]:
    if not isinstance(context, list) or len(context) > cfg.max_context_items:
        raise ValueError("invalid context")
    for item in context:
        if not isinstance(item, dict) or not item.keys() <= {"title", "url", "snippet"}:
            raise ValueError("invalid context item")
        for val in item.values():
            if not isinstance(val, str) or len(val) > cfg.max_message_length:
                raise ValueError("invalid context item")
    return context


def _validate_payload(payload: t.Any, cfg: SettingsAISummary) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Validate the request body of the ``/ai_summary`` endpoint and return
    the ``messages`` and ``context`` lists.  Raises a :py:obj:`ValueError` for
    any malformed payload."""

    if not isinstance(payload, dict):
        raise ValueError("payload is not an object")
    return _validate_messages(payload.get("messages"), cfg), _validate_context(payload.get("context", []), cfg)


def _open_upstream(client: httpx.Client, payload: dict[str, t.Any]) -> tuple[t.Any, t.Any]:
    """Start the streaming completion on the LLM server.

    Returns the (already entered) stream context and the response, or
    ``(None, None)`` if no usable response was received.

    The request is repeated (:py:obj:`UPSTREAM_RETRIES`) when the server did not
    answer in time, and when it answered ``5xx`` -- both mean *not right now*,
    and the most common reason is a model that is still being loaded.  A ``4xx``
    is not repeated: a wrong API key or an unknown model name does not become
    right when asked twice."""

    for attempt in range(UPSTREAM_RETRIES + 1):
        stream_ctx = client.stream("POST", "/chat/completions", json=payload)
        try:
            resp = stream_ctx.__enter__()  # pylint: disable=unnecessary-dunder-call
        except httpx.TransportError as exc:
            if attempt < UPSTREAM_RETRIES:
                log.debug("LLM server did not answer (%s), asking again", exc)
                continue
            log.warning("LLM server did not answer: %s", exc)
            return None, None
        except httpx.HTTPError as exc:
            log.warning("request to the LLM server failed: %s", exc)
            return None, None

        if resp.status_code == 200:
            return stream_ctx, resp

        # the body of an error response is short and usually names the cause,
        # e.g. an unknown model; without it a misconfiguration is invisible
        detail = ""
        try:
            resp.read()
            detail = resp.text.strip()[:200]
        except (httpx.HTTPError, UnicodeDecodeError):  # pragma: no cover
            pass
        stream_ctx.__exit__(None, None, None)

        # 5xx is the server saying it is not able to answer *right now* -- a
        # model still loading, a gateway with no upstream yet.  4xx is the
        # server saying the request is wrong, which a second one would be too.
        if resp.status_code >= 500 and attempt < UPSTREAM_RETRIES:
            log.debug("LLM server replied HTTP %s (%s), asking again", resp.status_code, detail)
            continue
        log.warning("LLM server responded with HTTP %s %s", resp.status_code, detail)
        return None, None

    return None, None  # pragma: no cover - the loop always returns


def ai_summary_view() -> flask.Response:
    """Stream an AI generated answer for the messages in the request body,
    response is NDJSON: ``{"delta": ..}`` lines followed by one final
    ``{"done": true, ..}`` line."""

    cfg: SettingsAISummary = get_setting("ai_summary")

    if SXNGPlugin.id not in sxng_request.user_plugins:
        return flask.Response(json.dumps({"error": "plugin is not enabled"}), status=403, mimetype="application/json")

    try:
        messages, context = _validate_payload(sxng_request.get_json(force=True, silent=True), cfg)
    except ValueError as exc:
        return _bad_request(str(exc))

    server = _user_server(sxng_request, cfg)
    if not _valid_server(server):
        return _bad_request("no valid LLM server configured")

    model = str(sxng_request.preferences.get_value("ai_summary_model") or "").strip() or cfg.model
    if not MODEL_NAME_REGEXP.fullmatch(model):
        return _bad_request("no valid model configured")

    chat_payload = {
        "model": model,
        "messages": build_chat_messages(cfg, messages, context),
        "stream": True,
    }

    # open the upstream connection before streaming, a connection error is
    # reported as HTTP 502 instead of a line in an already started stream
    user_api_key = str(sxng_request.preferences.get_value("ai_summary_api_key") or "").strip()
    client = _get_client(server, cfg, _server_api_key(cfg, server, user_api_key))
    stream_ctx, upstream = _open_upstream(client, chat_payload)
    if stream_ctx is None or upstream is None:
        client.close()
        return flask.Response(json.dumps({"error": "upstream error"}), status=502, mimetype="application/json")

    # from here on nothing must be read from the request context, the
    # generator runs after the request context has been torn down

    def ndjson(obj: dict[str, t.Any]) -> bytes:
        # the generator bypasses flask's response encoding (direct_passthrough)
        return (json.dumps(obj) + "\n").encode()

    def generate():
        start = time.monotonic()
        try:
            # the upstream is a SSE stream: "data: {..}" lines, terminated by
            # a "data: [DONE]" line
            for line in upstream.iter_lines():
                if time.monotonic() - start > cfg.stream_timeout:
                    yield ndjson({"done": True, "error": "timeout"})
                    return
                line = line.strip()
                if not line or line.startswith(":") or not line.startswith("data:"):
                    continue
                payload = line[len("data:") :].strip()
                if payload == "[DONE]":
                    break
                data = json.loads(payload)
                choices = data.get("choices") or [{}]
                delta = choices[0].get("delta", {}).get("content") or ""
                if delta:
                    yield ndjson({"delta": delta})
            yield ndjson({"done": True, "model": model})
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("error while streaming from the LLM server: %s", exc)
            yield ndjson({"done": True, "error": "upstream error"})
        finally:
            stream_ctx.__exit__(None, None, None)
            client.close()

    return flask.Response(
        generate(),
        mimetype="application/x-ndjson",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
        direct_passthrough=True,
    )
