# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

from __future__ import annotations
from hashlib import md5

import flask

from searx.data import ahmia_blacklist_loader
from searx import get_setting


name = "Ahmia blacklist"
description = "Filter out onion results that appear in Ahmia's blacklist. (See https://ahmia.fi/blacklist)"
default_on = True
preference_section = 'onions'

ahmia_blacklist: list = []


def on_result(_request, _search, result) -> bool:
    if not getattr(result, 'is_onion', None) or not getattr(result, 'parsed_url', None):
        return True
    result_hash = md5(result['parsed_url'].hostname.encode()).hexdigest()
    return result_hash not in ahmia_blacklist


def init(app=flask.Flask) -> bool:  # pylint: disable=unused-argument
    global ahmia_blacklist  # pylint: disable=global-statement
    if not get_setting("outgoing.using_tor_proxy"):
        # disable the plugin
        return False
    ahmia_blacklist = ahmia_blacklist_loader()
    return True
