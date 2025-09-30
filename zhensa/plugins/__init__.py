# SPDX-License-Identifier: AGPL-3.0-or-later
""".. sidebar:: Further reading ..

   - :ref:`plugins admin`
   - :ref:`Zhensa settings <settings plugins>`

Plugins can extend or replace functionality of various components of Zhensa.

Entry points (hooks) define when a plugin runs.  Right now only three hooks are
implemented.  So feel free to implement a hook if it fits the behaviour of your
plugin / a plugin doesn't need to implement all the hooks.

- pre search: :py:obj:`Plugin.pre_search`
- post search: :py:obj:`Plugin.post_search`
- on each result item: :py:obj:`Plugin.on_result`

Below you will find some examples, for more coding examples have a look at the
built-in plugins :origin:`zhensa/plugins/` or `Only show green hosted results`_.

.. _Only show green hosted results:
   https://github.com/return42/tgwf-zhensa-plugins/


Add Answer example
==================

Here is an example of a very simple plugin that adds a "Hello World" into the
answer area:

.. code:: python

   from flask_babel import gettext as _
   from zhensa.plugins import Plugin
   from zhensa.result_types import Answer

   class MyPlugin(Plugin):

       id = "hello world"

       def __init__(self, plg_cfg):
           super().__init__(plg_cfg)
           self.info = PluginInfo(id=self.id, name=_("Hello"), description=_("demo plugin"))

       def post_search(self, request, search):
           return [ Answer(answer="Hello World") ]

.. _filter urls example:

Filter URLs example
===================

.. sidebar:: Further reading ..

   - :py:obj:`Result.filter_urls(..) <zhensa.result_types._base.Result.filter_urls>`

The :py:obj:`Result.filter_urls(..) <zhensa.result_types._base.Result.filter_urls>`
can be used to filter and/or modify URL fields.  In the following example, the
filter function ``my_url_filter``:

.. code:: python

   def my_url_filter(result, field_name, url_src) -> bool | str:
       if "google" in url_src:
           return False              # remove URL field from result
       if "facebook" in url_src:
           new_url = url_src.replace("facebook", "fb-dummy")
           return new_url            # return modified URL
       return True                   # leave URL in field unchanged

is applied to all URL fields in the :py:obj:`Plugin.on_result` hook:

.. code:: python

   class MyUrlFilter(Plugin):
       ...
       def on_result(self, request, search, result) -> bool:
           result.filter_urls(my_url_filter)
           return True


Implementation
==============

.. autoclass:: Plugin
   :members:

.. autoclass:: PluginInfo
   :members:

.. autoclass:: PluginStorage
   :members:

.. autoclass:: PluginCfg
   :members:
"""


__all__ = ["PluginInfo", "Plugin", "PluginStorage", "PluginCfg"]


import zhensa
from ._core import PluginInfo, Plugin, PluginStorage, PluginCfg

STORAGE: PluginStorage = PluginStorage()


def initialize(app):
    STORAGE.load_settings(zhensa.get_setting("plugins"))
    STORAGE.init(app)
