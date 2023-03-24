# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""A plugin to check if the ip address of the request is a Tor exit-node if the
user searches for ``tor-check``.  It fetches the tor exit node list from
https://check.torproject.org/exit-addresses and parses all the IPs into a list,
then checks if the user's IP address is in it.

Enable in ``settings.yml``:

.. code:: yaml

  enabled_plugins:
    ..
    - 'Tor check plugin'

"""

import re
from flask_babel import gettext
from httpx import HTTPError
from searx.network import get

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


def post_search(request, search):

    if search.search_query.pageno > 1:
        return True

    if search.search_query.query.lower() == "tor-check":

        # Request the list of tor exit nodes.
        try:
            resp = get("https://check.torproject.org/exit-addresses")
            node_list = re.findall(reg, resp.text)

        except HTTPError:
            # No answer, return error
            search.result_container.answers["tor"] = {
                "answer": gettext(
                    "Could not download the list of Tor exit-nodes from: https://check.torproject.org/exit-addresses"
                )
            }
            return True

        x_forwarded_for = request.headers.getlist("X-Forwarded-For")

        if x_forwarded_for:
            ip_address = x_forwarded_for[0]
        else:
            ip_address = request.remote_addr

        if ip_address in node_list:
            search.result_container.answers["tor"] = {
                "answer": gettext(
                    "You are using Tor and it looks like you have this external IP address: {ip_address}".format(
                        ip_address=ip_address
                    )
                )
            }
        else:
            search.result_container.answers["tor"] = {
                "answer": gettext(
                    "You are not using Tor and you have this external IP address: {ip_address}".format(
                        ip_address=ip_address
                    )
                )
            }

    return True
