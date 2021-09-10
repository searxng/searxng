# SPDX-License-Identifier: AGPL-3.0-or-later

import re
from urllib.parse import urlunparse
from searx import settings
from searx.plugins import logger
from flask_babel import gettext

name = gettext('Hostname replace')
description = gettext('Rewrite result hostnames or remove results based on the hostname')
default_on = False
preference_section = 'general'

plugin_id = 'hostname_replace'

replacements = {re.compile(p): r for (p, r) in settings[plugin_id].items()} if plugin_id in settings else {}

logger = logger.getChild(plugin_id)
parsed = 'parsed_url'


def on_result(request, search, result):
    if parsed not in result:
        return True
    for (pattern, replacement) in replacements.items():
        if pattern.search(result[parsed].netloc):
            if not replacement:
                return False
            result[parsed] = result[parsed]._replace(netloc=pattern.sub(replacement, result[parsed].netloc))
            result['url'] = urlunparse(result[parsed])

    return True
