'''
 SPDX-License-Identifier: AGPL-3.0-or-later
'''

from hashlib import md5
from searx.data import ahmia_blacklist_loader

name = "Ahmia blacklist"
description = "Filter out onion results that appear in Ahmia's blacklist. (See https://ahmia.fi/blacklist)"
default_on = True
preference_section = 'onions'

ahmia_blacklist = None


def get_ahmia_blacklist():
    global ahmia_blacklist
    if not ahmia_blacklist:
        ahmia_blacklist = ahmia_blacklist_loader()
    return ahmia_blacklist


def on_result(request, search, result):
    if not result.get('is_onion') or not result.get('parsed_url'):
        return True
    result_hash = md5(result['parsed_url'].hostname.encode()).hexdigest()
    return result_hash not in get_ahmia_blacklist()
