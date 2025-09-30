# SPDX-License-Identifier: AGPL-3.0-or-later
"""The builtin types that are added to the global namespace of a module by the
intended monkey patching of the engine modules.

.. attention::

   Monkey-patching modules is a practice from the past that shouldn't be
   expanded upon.  In the long run, there should be an engine class that can be
   inherited.  However, as long as this class doesn't exist, and as long as all
   engine modules aren't converted to an engine class, these builtin types will
   still be needed.
"""

import logging
from zhensa.enginelib import traits as _traits

logger: logging.Logger
supported_languages: str
language_aliases: str
language_support: bool
traits: _traits.EngineTraits

# from zhensa.engines.ENGINE_DEFAULT_ARGS
about: dict[str, dict[str, str | None | bool]]
categories: list[str]
disabled: bool
display_error_messages: bool
enable_http: bool
engine_type: str
inactive: bool
max_page: int
paging: int
safesearch: int
send_accept_language_header: bool
shortcut: str
time_range_support: int
timeout: int
tokens: list[str]
using_tor_proxy: bool

# from zhensa.engines.check_engine_module
network: str

# from zhensa.engines.update_attributes_for_tor
search_url: str
