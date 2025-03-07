# SPDX-License-Identifier: AGPL-3.0-or-later
"""A plugin to check if the ip address of the request is a Tor exit-node if the
user searches for ``tor-check``.  It fetches the tor exit node list from
:py:obj:`url_exit_list` and parses all the IPs into a list, then checks if the
user's IP address is in it.

Enable in ``settings.yml``:

.. code:: yaml

  enabled_plugins:
    ..
    - 'Tor check plugin'

"""

from __future__ import annotations

import re
from flask_babel import gettext
from httpx import HTTPError

from searx.network import get
from searx.result_types import EngineResults
from searx.botdetection import get_real_ip


default_on = False

name = gettext("Tor check plugin")
'''Translated name of the plugin'''

description = gettext(
    "This plugin checks if the address of the request is a Tor exit-node, and"
    " informs the user if it is; like check.torproject.org, but from SearXNG."
)
'''Translated description of the plugin.'''

preference_section = 'query'
'''The preference section where the plugin is shown.'''

query_keywords = ['tor-check']
'''Query keywords shown in the preferences.'''

query_examples = ''
'''Query examples shown in the preferences.'''

# Regex for exit node addresses in the list.
reg = re.compile(r"(?<=ExitAddress )\S+")

url_exit_list = "https://check.torproject.org/exit-addresses"
"""URL to load Tor exit list from."""


def post_search(request, search) -> EngineResults:
    results = EngineResults()

    if search.search_query.pageno > 1:
        return results

    if search.search_query.query.lower() == "tor-check":

        # Request the list of tor exit nodes.
        try:
            resp = get(url_exit_list)
            node_list = re.findall(reg, resp.text)  # type: ignore

        except HTTPError:
            # No answer, return error
            msg = gettext("Could not download the list of Tor exit-nodes from")
            results.add(results.types.Answer(answer=f"{msg} {url_exit_list}"))
            return results

        real_ip = get_real_ip(request)

        if real_ip in node_list:
            msg = gettext("You are using Tor and it looks like you have the external IP address")
            results.add(results.types.Answer(answer=f"{msg} {real_ip}"))

        else:
            msg = gettext("You are not using Tor and you have the external IP address")
            results.add(results.types.Answer(answer=f"{msg} {real_ip}"))

    return results
