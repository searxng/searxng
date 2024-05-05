# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

import re
from urllib.parse import urlunparse, urlparse

from flask_babel import gettext

from searx import settings
from searx.plugins import logger

name = gettext('Hostnames plugin')
description = gettext('Rewrite hostnames, remove results or prioritize them based on the hostname')
default_on = False
preference_section = 'general'

plugin_id = 'hostnames'

replacements = {
    re.compile(p): r
    for (p, r) in (settings.get(plugin_id, {}).get('replace', settings.get('hostname_replace', {})).items())
}
removables = {re.compile(p) for p in settings[plugin_id].get('remove', [])}
high_priority = {re.compile(p) for p in settings[plugin_id].get('high_priority', [])}
low_priority = {re.compile(p) for p in settings[plugin_id].get('low_priority', [])}

logger = logger.getChild(plugin_id)
parsed = 'parsed_url'
_url_fields = ['iframe_src', 'audio_src']


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
