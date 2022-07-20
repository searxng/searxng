# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Rewrite result hostnames or remove results based on the hostname.

``/etc/searxng/settings.yml``
  Deactivate by default, activate plugin and append entries to the
  list ``hostname_replace``

.. code-block:: yaml

   enabled_plugins:
     - 'Hostname replace'  # see hostname_replace configuration below
     # ...

.. _#911: https://github.com/searxng/searxng/discussions/911
.. _#970: https://github.com/searxng/searxng/discussions/970

Configuration of the replacements (`#911`_, `#970`_)

.. code-block:: yaml

  hostname_replace:
    # to ignore result from codegrepper.com
    '(.*\\.)?codegrepper\\.com': false

    # redirect youtube links to a invidio instance
    '(.*\\.)?youtube\\.com$': 'invidio.xamh.de'
    '(.*\\.)?youtube-nocookie\\.com$': 'invidio.xamh.de'

"""

import re
from urllib.parse import urlunparse, urlparse
from flask_babel import gettext

from searx import settings
from searx.plugins import logger
from searx.results.container import is_standard_result
from searx.results.infobox import infobox_modify_url, is_infobox
from searx.results.answer import answer_modify_url, is_answer


name = gettext('Hostname replace')
description = gettext('Rewrite result hostnames or remove results based on the hostname')
default_on = False
preference_section = 'general'

plugin_id = 'hostname_replace'

replacements = {re.compile(p): r for (p, r) in settings[plugin_id].items()} if plugin_id in settings else {}

logger = logger.getChild(plugin_id)
parsed = 'parsed_url'


def on_result(_request, _search, result):

    for (pattern, replacement) in replacements.items():
        # pylint: disable=cell-var-from-loop

        def modify_url(url):
            url_src = urlparse(url)
            if not pattern.search(url_src.netloc):
                return url
            if not replacement:
                return None
            url_src = url_src._replace(netloc=pattern.sub(replacement, url_src.netloc))
            return urlunparse(url_src)

        if is_infobox(result):
            infobox_modify_url(modify_url, result)
            continue

        if is_answer(result):
            answer_modify_url(modify_url, result)
            continue

        if is_standard_result(result):
            if parsed in result:
                if pattern.search(result[parsed].netloc):
                    # to keep or remove this result from the result list depends
                    # (only) on the 'parsed_url'
                    if not replacement:
                        return False
                result[parsed] = result[parsed]._replace(netloc=pattern.sub(replacement, result[parsed].netloc))
                result['url'] = urlunparse(result[parsed])

            for url_field in ['iframe_src', 'audio_src']:
                url = result.get(url_field)
                if url:
                    _url = modify_url(url)
                    if _url is None:
                        del result[url]
                    elif _url != url:
                        result[url_field] = url
    return True
