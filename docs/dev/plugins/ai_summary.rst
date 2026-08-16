.. _ai_summary plugin:

==========
AI Summary
==========

.. sidebar:: Further reading ..

   - :ref:`Configuration <settings ai_summary>`
   - :ref:`dev plugin`
   - :ref:`result types`

The AI Summary plugin shows a generated answer above the ordinary search
results.  The text comes from an LLM server run by the administrator, which
speaks the `OpenAI chat completions API`_ -- `Ollama`_, Hugging Face TGI,
LiteLLM, vLLM, llama.cpp and anything else implementing that specification.
See :ref:`its configuration <settings ai_summary>` for how to set one up.

The summary is generated asynchronously: the result page is delivered without
delay and carries an empty placeholder, which the browser fills from a second,
streaming request.

Request flow
============

.. _ai_summary dataflow:

.. kernel-render:: DOT
   :alt: Data flow between browser, SearXNG and the LLM server
   :caption: A search that produces a summary: two requests, not one

   digraph ai_summary {
     rankdir=LR;
     graph [fontname="sans-serif", ranksep=1.1, nodesep=0.4];
     node  [fontname="sans-serif", fontsize=11, shape=box, style="rounded,filled",
            fillcolor="#f4f4f4", color="#999999"];
     edge  [fontname="sans-serif", fontsize=9, color="#666666"];

     browser  [label="browser"];
     searxng  [label="SearXNG"];
     engines  [label="search engines", fillcolor="#ffffff"];
     llm      [label="LLM server\nOllama, vLLM, ...", fillcolor="#ffffff"];

     browser -> searxng [label=" 1  GET /search"];
     searxng -> engines [label=" 2  query"];
     searxng -> browser [label=" 3  result page,\l    empty summary box\l", constraint=false];
     browser -> searxng [label=" 4  POST /ai_summary\l    (query + results)\l"];
     searxng -> llm     [label=" 5  POST /v1/chat/completions"];
     llm     -> searxng [label=" 6  SSE token stream", constraint=false];
     searxng -> browser [label=" 7  NDJSON token stream", constraint=false];
   }

Steps 1 to 3 are an ordinary SearXNG search.  :py:obj:`SXNGPlugin.post_search
<searx.plugins.ai_summary.SXNGPlugin.post_search>` adds an empty
:py:obj:`searx.result_types.AiSummary` placeholder to the answer area and
returns; the result page is not delayed.

Steps 4 to 7 run in the browser once the page is rendered.
``client/simple/src/js/plugin/AiSummary.ts`` posts to the ``/ai_summary``
endpoint (registered in :py:obj:`searx.webapp`), which opens a streaming
request to the LLM server and re-emits the tokens as they arrive.

The two streams use different formats.  The LLM server sends `SSE`_ --
``data: {...}`` lines terminated by ``data: [DONE]``.  SearXNG re-emits them to
the browser as `NDJSON`_: one JSON object per line, ``{"delta": "..."}`` for
each chunk of text and a final ``{"done": true}``.

When no summary is generated
============================

:py:obj:`SXNGPlugin.post_search
<searx.plugins.ai_summary.SXNGPlugin.post_search>` adds no placeholder for:

- page two and beyond
- categories other than *general*
- non-HTML output formats (the JSON, CSV and RSS APIs)
- queries an engine already answered with an infobox (wikipedia, wikidata) or
  an instant answer (e.g. ddg definitions)
- an empty query, or no LLM server configured

API keys
========

The administrator's ``api_key`` is sent only to the configured ``base_url``.
Users who point the ``ai_summary_server`` preference at a server of their own
authenticate it with their own ``ai_summary_api_key`` preference, which is
stored in a cookie and excluded from the preferences URL; the administrator's
key is never sent to such a server.  A server URL carrying credentials in its
userinfo is ignored, and the administrator's default is used instead.

:py:obj:`_server_api_key <searx.plugins.ai_summary._server_api_key>` implements
the rule.

Reference
=========

.. automodule:: searx.plugins.ai_summary
   :members:

.. _Ollama: https://ollama.com/
.. _OpenAI chat completions API: https://platform.openai.com/docs/api-reference/chat
.. _SSE: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
.. _NDJSON: https://github.com/ndjson/ndjson-spec
