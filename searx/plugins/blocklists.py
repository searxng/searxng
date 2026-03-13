# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=line-too-long
"""At startup, this plugin downloads all files configured in ``blocklists:`` and
parses them as Easylist filter files. Easylist is a common format for Adblock
Rules, e.g. used by Adblock Plus, Adguard and uBlock Origin.

The configuration syntax is as follows:

.. code-block:: yaml

   blocklists:
     - "https://raw.githubusercontent.com/alvi-se/ai-ublock-blacklist/refs/heads/master/list.txt"

All results that match any of the rules specified in ``list.txt`` will now be
removed from the search results.

.. hint::
   Please make sure that the filter lists are not that large in size (less than
   2000 entries if possible) - otherwise this has a very big impact on search
   performance, i.e. will slow it down drastically.

If you want to manually configure which URLs should be blocked instead of using premade blocklists, please see the :ref:`hostnames plugin`.
"""

import typing as t

import time
from gettext import gettext

import searx.easylist
from searx import settings, logger
from searx.easylist import EasylistFilterRule
from searx.plugins import Plugin, PluginInfo
from searx.network import get

if t.TYPE_CHECKING:
    import flask
    from searx.search import SearchWithPlugins
    from searx.extended_types import SXNG_Request
    from searx.result_types import Result
    from searx.plugins import PluginCfg

EXCEPTION_RULES: set[EasylistFilterRule] = set()
FILTER_RULES: set[EasylistFilterRule] = set()


class SXNGPlugin(Plugin):
    """Block results by their URL based on Easylist filter lists"""

    id = "blocklists"

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__(plg_cfg)
        self.info = PluginInfo(
            id=self.id,
            name=gettext("Blocklists plugin"),
            description=gettext("Removes results based on Easylist blocklists"),
            preference_section="general",
        )

    def on_result(self, request: "SXNG_Request", search: "SearchWithPlugins", result: "Result") -> bool:
        if not result.parsed_url:
            return True

        start = time.time()
        for rule in EXCEPTION_RULES:
            if rule.matches_url(result.parsed_url):
                return True

        for rule in FILTER_RULES:
            if rule.matches_url(result.parsed_url):
                return False

        logger.debug(time.time() - start)
        return True

    def init(self, app: "flask.Flask") -> bool:  # pylint: disable=unused-argument
        filter_list_urls = settings.get(self.id, {})
        if not isinstance(filter_list_urls, list):
            return False

        for url in filter_list_urls:
            plain_rule_list = load_list_from_web(url)

            for line in plain_rule_list.splitlines():
                rule = searx.easylist.parse(line)
                if not rule:
                    continue

                if rule.is_exception:
                    EXCEPTION_RULES.add(rule)
                else:
                    FILTER_RULES.add(rule)

        return True


def load_list_from_web(url: str) -> str:
    """
    Download a filterlist file from the provided ``url``.
    """
    # TODO: Currently, the filter lists are not cached  # pylint: disable=fixme
    # that should be changed in the future to reduce startup times and network usage.
    resp = get(url)

    if not resp.ok:
        raise IOError(f"failed to load filterlist from '{url}'")

    return resp.text
