.. _settings ai_summary:

===============
``ai_summary:``
===============

.. sidebar:: Further reading ..

   - :ref:`ai_summary plugin`
   - :ref:`settings plugins`
   - :ref:`settings preferences`

Configuration of the :ref:`AI Summary plugin <ai_summary plugin>`, which shows a
short AI generated answer above the search results.

The text is produced by an LLM server that you run; SearXNG ships no model and
contacts no AI provider of its own.  Any server implementing the `OpenAI chat
completions API`_ works: `Ollama`_, vLLM, llama.cpp, LM Studio, Hugging Face
TGI and others.  The plugin is not activated by default.

.. _ai_summary quickstart:

Quickstart
==========

A local setup on the same machine as SearXNG, in four steps.

**1. Install Ollama**

.. code:: sh

   curl -fsSL https://ollama.com/install.sh | sh

**2. Download a model**

.. code:: sh

   ollama pull gemma3:4b

``gemma3:4b`` needs roughly 4 GB of memory and runs on CPU if you have no GPU.
On a smaller machine use ``gemma3:1b``; any model in the `Ollama library`_
works.

**3. Configure SearXNG**

Add this to your ``settings.yml``:

.. code:: yaml

   ai_summary:
     base_url: "http://127.0.0.1:11434"
     model: "gemma3:4b"

   plugins:
     searx.plugins.ai_summary.SXNGPlugin:
       active: true
     # keep the plugins you already had, see the warning below
     searx.plugins.calculator.SXNGPlugin: {active: true}
     searx.plugins.hash_plugin.SXNGPlugin: {active: true}
     searx.plugins.self_info.SXNGPlugin: {active: true}
     searx.plugins.unit_converter.SXNGPlugin: {active: true}
     searx.plugins.ahmia_filter.SXNGPlugin: {active: true}
     searx.plugins.hostnames.SXNGPlugin: {active: true}
     searx.plugins.time_zone.SXNGPlugin: {active: true}
     searx.plugins.tracker_url_remover.SXNGPlugin: {active: true}
     searx.plugins.infinite_scroll.SXNGPlugin: {active: false}
     searx.plugins.oa_doi_rewrite.SXNGPlugin: {active: false}
     searx.plugins.tor_check.SXNGPlugin: {active: false}

.. warning::

   A ``plugins:`` block **replaces** the default list, it is not merged into it
   (:ref:`settings plugins`).  Listing only the AI Summary plugin switches
   every other plugin off, which is why the block above repeats the defaults --
   drop the lines for plugins you do not want.

**4. Restart SearXNG** and search for something.

The summary appears above the results while it is still being written.

Options
=======

Only ``base_url`` is required.  A model is needed too, but if ``model`` is left
empty the first entry of ``models`` is used.

.. code:: yaml

   ai_summary:
     base_url: "http://127.0.0.1:11434"
     model: "gemma3:4b"
     grounding: true

.. autoclass:: searx.ai_summary.SettingsAISummary
   :members:

Servers that require authentication
===================================

vLLM and llama.cpp started with ``--api-key``, a gateway such as LiteLLM, or an
LLM server behind an authenticating reverse proxy all expect a key.  Set it
with ``api_key``:

.. code:: yaml

   ai_summary:
     base_url: "http://127.0.0.1:8000"
     api_key: "sk-..."
     model: "gemma3:4b"

The key is sent as an ``Authorization: Bearer`` header and only to the server in
``base_url``.  Users who configure a server of their own in the
``ai_summary_server`` preference never receive it; they set their own key in the
``ai_summary_api_key`` preference.

SearXNG has no separate secret store, so the key is held in ``settings.yml`` --
that file should be readable only by the user SearXNG runs as.

.. _ai_summary grounding:

Grounding
=========

With ``grounding`` enabled, which is the default, the query **and the top search
results** (title, URL and snippet, at most ``max_context_items`` of them) are
sent to the LLM server, and the answer reflects what the search found.  With it
disabled only the query is sent and the model answers from its training data.
Users can change this in the ``ai_summary_grounding`` preference.

What leaves the network therefore depends on where the LLM server runs: with a
server on localhost or in the local network, nothing does.

Public SearXNG instances
========================

The server URL, model and API key are user preferences so that someone running
SearXNG at home can switch models or debug their LLM server from the
preferences page, without editing ``settings.yml`` and restarting.

On public SearXNG instances, those same preferences let any visitor choose the
address the summary request is sent to.  The request is made by the SearXNG
host, so a visitor can use it to reach machines on your network that they have
no route to themselves -- an `SSRF`_ vector.

.. attention::

   Lock ``ai_summary_server`` on any SearXNG instance that is reachable by
   people outside your household.

Locking a preference makes SearXNG use your configured value and ignore the
user's (:ref:`settings preferences`):

.. code:: yaml

   preferences:
     lock:
       - ai_summary_server
       - ai_summary_api_key
       - ai_summary_model
       - ai_summary_grounding

``ai_summary_server`` is the one that matters: locking it closes the SSRF
vector.  Locking ``ai_summary_api_key`` additionally stops visitors making your
SearXNG instance send an ``Authorization`` header of their choosing to a host of
their choosing.  ``ai_summary_model`` and ``ai_summary_grounding`` are about
cost and consistency rather than security.

.. _Ollama: https://ollama.com/
.. _Ollama library: https://ollama.com/library
.. _OpenAI chat completions API: https://platform.openai.com/docs/api-reference/chat
.. _SSRF: https://owasp.org/www-community/attacks/Server_Side_Request_Forgery
