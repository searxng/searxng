# SPDX-License-Identifier: AGPL-3.0-or-later
"""A plugin to check if the ip address of the request is a Tor exit-node if the
user searches for ``tor-check``.  It fetches the tor exit node list from
:py:obj:`url_exit_list` and parses all the IPs into a list, then checks if the
user's IP address is in it.
"""
from ipaddress import ip_address
import typing

import re
from flask_babel import gettext
from httpx import HTTPError

from zhensa.network import get
from zhensa.plugins import Plugin, PluginInfo
from zhensa.result_types import EngineResults

if typing.TYPE_CHECKING:
    from zhensa.search import SearchWithPlugins
    from zhensa.extended_types import SXNG_Request
    from zhensa.plugins import PluginCfg


# Regex for exit node addresses in the list.
reg = re.compile(r"(?<=ExitAddress )\S+")

url_exit_list = "https://check.torproject.org/exit-addresses"
"""URL to load Tor exit list from."""


class SXNGPlugin(Plugin):
    """Rewrite hostnames, remove results or prioritize them."""

    id = "tor_check"
    keywords = ["tor-check", "tor_check", "torcheck", "tor", "tor check"]

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__(plg_cfg)
        self.info = PluginInfo(
            id=self.id,
            name=gettext("Tor check plugin"),
            description=gettext(
                "This plugin checks if the address of the request is a Tor exit-node, and"
                " informs the user if it is; like check.torproject.org, but from Zhensa."
            ),
            preference_section="query",
        )

    def post_search(self, request: "SXNG_Request", search: "SearchWithPlugins") -> EngineResults:
        results = EngineResults()

        if search.search_query.pageno > 1:
            return results

        if search.search_query.query.lower() in self.keywords:

            # Request the list of tor exit nodes.
            try:
                resp = get(url_exit_list)
                node_list = re.findall(reg, resp.text)  # type: ignore

            except HTTPError:
                # No answer, return error
                msg = gettext("Could not download the list of Tor exit-nodes from")
                results.add(results.types.Answer(answer=f"{msg} {url_exit_list}"))
                return results

            real_ip = ip_address(address=str(request.remote_addr)).compressed

            if real_ip in node_list:
                msg = gettext("You are using Tor and it looks like you have the external IP address")
                results.add(results.types.Answer(answer=f"{msg} {real_ip}"))

            else:
                msg = gettext("You are not using Tor and you have the external IP address")
                results.add(results.types.Answer(answer=f"{msg} {real_ip}"))

        return results
