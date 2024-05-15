# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

from flask_babel import gettext
from searx.plugins import logger

name = gettext('Hostname replace')
description = "Deprecated / contact system admin to configure 'Hostnames plugin'!!"
default_on = False
preference_section = 'general'

plugin_id = 'hostname_replace'
logger = logger.getChild(plugin_id)

REPORTED = False


def deprecated_msg():
    global REPORTED  # pylint: disable=global-statement
    if REPORTED:
        return
    logger.error(
        "'Hostname replace' plugin is deprecated and will be dropped soon!"
        " Configure 'Hostnames plugin':"
        " https://docs.searxng.org/src/searx.plugins.hostnames.html"
    )
    REPORTED = True


def on_result(_request, _search, result):
    # pylint: disable=import-outside-toplevel, cyclic-import
    from searx.plugins.hostnames import on_result as hostnames_on_result

    deprecated_msg()
    return hostnames_on_result(_request, _search, result)
