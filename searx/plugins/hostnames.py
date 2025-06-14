# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=too-many-branches, unused-argument
"""

During the initialization phase, the plugin checks whether a ``hostnames:``
configuration exists. If this is not the case, the plugin is not included
in the PluginStorage (it is not available for selection).

- ``hostnames.replace``: A **mapping** of regular expressions to hostnames to be
  replaced by other hostnames.

  .. code:: yaml

     hostnames:
       replace:
         '(.*\\.)?youtube\\.com$': 'invidious.example.com'
         '(.*\\.)?youtu\\.be$': 'invidious.example.com'
         ...

- ``hostnames.remove``: A **list** of regular expressions of the hostnames whose
  results should be taken from the results list.

  .. code:: yaml

     hostnames:
       remove:
         - '(.*\\.)?facebook.com$'
         - ...

- ``hostnames.high_priority``: A **list** of regular expressions for hostnames
  whose result should be given higher priority. The results from these hosts are
  arranged higher in the results list.

  .. code:: yaml

     hostnames:
       high_priority:
         - '(.*\\.)?wikipedia.org$'
         - ...

- ``hostnames.lower_priority``: A **list** of regular expressions for hostnames
  whose result should be given lower priority. The results from these hosts are
  arranged lower in the results list.

  .. code:: yaml

     hostnames:
       low_priority:
         - '(.*\\.)?google(\\..*)?$'
         - ...

If the URL matches the pattern of ``high_priority`` AND ``low_priority``, the
higher priority wins over the lower priority.

Alternatively, you can also specify a file name for the **mappings** or
**lists** to load these from an external file:

.. code:: yaml

   hostnames:
     replace: 'rewrite-hosts.yml'
     remove:
       - '(.*\\.)?facebook.com$'
       - ...
     low_priority:
       - '(.*\\.)?google(\\..*)?$'
       - ...
     high_priority:
       - '(.*\\.)?wikipedia.org$'
       - ...

The ``rewrite-hosts.yml`` from the example above must be in the folder in which
the ``settings.yml`` file is already located (``/etc/searxng``). The file then
only contains the lists or the mapping tables without further information on the
namespaces.  In the example above, this would be a mapping table that looks
something like this:

.. code:: yaml

   '(.*\\.)?youtube\\.com$': 'invidious.example.com'
   '(.*\\.)?youtu\\.be$': 'invidious.example.com'

"""

from __future__ import annotations
import typing

import re
from urllib.parse import urlunparse, urlparse

from flask_babel import gettext

from searx import settings
from searx.result_types._base import MainResult, LegacyResult
from searx.settings_loader import get_yaml_cfg
from searx.plugins import Plugin, PluginInfo

from ._core import log

if typing.TYPE_CHECKING:
    import flask
    from searx.search import SearchWithPlugins
    from searx.extended_types import SXNG_Request
    from searx.result_types import Result
    from searx.plugins import PluginCfg


REPLACE: dict[re.Pattern, str] = {}
REMOVE: set = set()
HIGH: set = set()
LOW: set = set()


class SXNGPlugin(Plugin):
    """Rewrite hostnames, remove results or prioritize them."""

    id = "hostnames"

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__(plg_cfg)
        self.info = PluginInfo(
            id=self.id,
            name=gettext("Hostnames plugin"),
            description=gettext("Rewrite hostnames and remove or prioritize results based on the hostname"),
            preference_section="general",
        )

    def on_result(self, request: "SXNG_Request", search: "SearchWithPlugins", result: Result) -> bool:

        for pattern in REMOVE:
            if result.parsed_url and pattern.search(result.parsed_url.netloc):
                # if the link (parsed_url) of the result match, then remove the
                # result from the result list, in any other case, the result
                # remains in the list / see final "return True" below.
                # log.debug("FIXME: remove [url/parsed_url] %s %s", pattern.pattern, result.url)
                return False

        result.filter_urls(filter_url_field)

        if isinstance(result, (MainResult, LegacyResult)):
            for pattern in LOW:
                if result.parsed_url and pattern.search(result.parsed_url.netloc):
                    result.priority = "low"

            for pattern in HIGH:
                if result.parsed_url and pattern.search(result.parsed_url.netloc):
                    result.priority = "high"

        return True

    def init(self, app: "flask.Flask") -> bool:  # pylint: disable=unused-argument
        global REPLACE, REMOVE, HIGH, LOW  # pylint: disable=global-statement

        if not settings.get(self.id):
            # Remove plugin, if there isn't a "hostnames:" setting
            return False

        REPLACE = self._load_regular_expressions("replace") or {}  # type: ignore
        REMOVE = self._load_regular_expressions("remove") or set()  # type: ignore
        HIGH = self._load_regular_expressions("high_priority") or set()  # type: ignore
        LOW = self._load_regular_expressions("low_priority") or set()  # type: ignore

        return True

    def _load_regular_expressions(self, settings_key) -> dict[re.Pattern, str] | set | None:
        setting_value = settings.get(self.id, {}).get(settings_key)

        if not setting_value:
            return None

        # load external file with configuration
        if isinstance(setting_value, str):
            setting_value = get_yaml_cfg(setting_value)

        if isinstance(setting_value, list):
            return {re.compile(r) for r in setting_value}

        if isinstance(setting_value, dict):
            return {re.compile(p): r for (p, r) in setting_value.items()}

        return None


def filter_url_field(result: "Result|LegacyResult", field_name: str, url_src: str) -> bool | str:
    """Returns bool ``True`` to use URL unchanged (``False`` to ignore URL).
    If URL should be modified, the returned string is the new URL to use."""

    if not url_src:
        log.debug("missing a URL in field %s", field_name)
        return True

    url_src_parsed = urlparse(url=url_src)

    for pattern in REMOVE:
        if pattern.search(url_src_parsed.netloc):
            return False

    for pattern, replacement in REPLACE.items():
        if pattern.search(url_src_parsed.netloc):
            new_url = url_src_parsed._replace(netloc=pattern.sub(replacement, url_src_parsed.netloc))
            new_url = urlunparse(new_url)
            return new_url

    return True
