# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=too-many-branches
"""In addition to rewriting/replace reslut URLs, the *hoostnames* plugin offers
other features.

- ``hostnames.replace``: A mapping of regular expressions to hostnames to be
  replaced by other hostnames.

- ``hostnames.remove``: A list of regular expressions of the hostnames whose
  results should be taken from the results list.

- ``hostnames.high_priority``: A list of regular expressions for hostnames whose
  result should be given higher priority. The results from these hosts are
  arranged higher in the results list.

- ``hostnames.lower_priority``: A list of regular expressions for hostnames
  whose result should be given lower priority. The results from these hosts are
  arranged lower in the results list.

Alternatively, a file name can also be specified for the mappings or lists:

.. code:: yaml

   hostnames:
     replace: 'rewrite-hosts.yml'
     remove:
       - '(.*\\.)?facebook.com$'
       ...
     low_priority:
       - '(.*\\.)?google(\\..*)?$'
       ...
     high_priority:
       - '(.*\\.)?wikipedia.org$'
       ...

The ``rewrite-hosts.yml`` from the example above must be in the folder in which
the ``settings.yml`` file is already located (``/etc/searxng``). The file then
only contains the lists or the mapping tables without further information on the
namespaces.  In the example above, this would be a mapping table that looks
something like this:

.. code:: yaml

   '(.*\\.)?youtube\\.com$': 'invidious.example.com'
   '(.*\\.)?youtu\\.be$': 'invidious.example.com'

"""

import re
from urllib.parse import urlunparse, urlparse

from flask_babel import gettext

from searx import settings
from searx.plugins import logger
from searx.settings_loader import get_yaml_file

name = gettext('Hostnames plugin')
description = gettext('Rewrite hostnames, remove results or prioritize them based on the hostname')
default_on = False
preference_section = 'general'

plugin_id = 'hostnames'

logger = logger.getChild(plugin_id)
parsed = 'parsed_url'
_url_fields = ['iframe_src', 'audio_src']


def _load_regular_expressions(settings_key):
    setting_value = settings.get(plugin_id, {}).get(settings_key)

    if not setting_value:
        return {}

    # load external file with configuration
    if isinstance(setting_value, str):
        setting_value = get_yaml_file(setting_value)

    if isinstance(setting_value, list):
        return {re.compile(r) for r in setting_value}

    if isinstance(setting_value, dict):
        return {re.compile(p): r for (p, r) in setting_value.items()}

    return {}


replacements = _load_regular_expressions('replace')
removables = _load_regular_expressions('remove')
high_priority = _load_regular_expressions('high_priority')
low_priority = _load_regular_expressions('low_priority')


def _matches_parsed_url(result, pattern):
    return parsed in result and pattern.search(result[parsed].netloc)


def on_result(_request, _search, result):
    for pattern, replacement in replacements.items():
        if _matches_parsed_url(result, pattern):
            logger.debug(result['url'])
            result[parsed] = result[parsed]._replace(netloc=pattern.sub(replacement, result[parsed].netloc))
            result['url'] = urlunparse(result[parsed])
            logger.debug(result['url'])

        for url_field in _url_fields:
            if not result.get(url_field):
                continue

            url_src = urlparse(result[url_field])
            if pattern.search(url_src.netloc):
                url_src = url_src._replace(netloc=pattern.sub(replacement, url_src.netloc))
                result[url_field] = urlunparse(url_src)

    for pattern in removables:
        if _matches_parsed_url(result, pattern):
            return False

        for url_field in _url_fields:
            if not result.get(url_field):
                continue

            url_src = urlparse(result[url_field])
            if pattern.search(url_src.netloc):
                del result[url_field]

    for pattern in low_priority:
        if _matches_parsed_url(result, pattern):
            result['priority'] = 'low'

    for pattern in high_priority:
        if _matches_parsed_url(result, pattern):
            result['priority'] = 'high'

    return True
