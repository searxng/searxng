# SPDX-License-Identifier: AGPL-3.0-or-later
""".. sidebar:: Further reading ..

   - :ref:`plugins admin`
   - :ref:`SearXNG settings <settings plugins>`
   - :ref:`builtin plugins`

Plugins can extend or replace functionality of various components of SearXNG.
Here is an example of a very simple plugin that adds a "Hello" into the answer
area:

.. code:: python

   from flask_babel import gettext as _
   from searx.plugins import Plugin
   from searx.result_types import Answer

   class MyPlugin(Plugin):

       id = "self_info"
       default_on = True

       def __init__(self):
           super().__init__()
           info = PluginInfo(id=self.id, name=_("Hello"), description=_("demo plugin"))

       def post_search(self, request, search):
           return [ Answer(answer="Hello") ]

Entry points (hooks) define when a plugin runs.  Right now only three hooks are
implemented.  So feel free to implement a hook if it fits the behaviour of your
plugin / a plugin doesn't need to implement all the hooks.

- pre search: :py:obj:`Plugin.pre_search`
- post search: :py:obj:`Plugin.post_search`
- on each result item: :py:obj:`Plugin.on_result`

For a coding example have a look at :ref:`self_info plugin`.

----

.. autoclass:: Plugin
   :members:

.. autoclass:: PluginInfo
   :members:

.. autoclass:: PluginStorage
   :members:

.. autoclass:: searx.plugins._core.ModulePlugin
   :members:
   :show-inheritance:

"""

from __future__ import annotations

__all__ = ["PluginInfo", "Plugin", "PluginStorage"]

from ._core import PluginInfo, Plugin, PluginStorage

STORAGE: PluginStorage = PluginStorage()


def initialize(app):
    STORAGE.load_builtins()
    STORAGE.init(app)
