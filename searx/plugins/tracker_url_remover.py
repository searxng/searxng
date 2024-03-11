# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

import re
from urllib.parse import urlunparse, parse_qsl, urlencode

from flask_babel import gettext

regexes = {
    re.compile(r'utm_[^&]+'),
    re.compile(r'(wkey|wemail)[^&]*'),
    re.compile(r'(_hsenc|_hsmi|hsCtaTracking|__hssc|__hstc|__hsfp)[^&]*'),
    re.compile(r'&$'),
}

name = gettext('Tracker URL remover')
description = gettext('Remove trackers arguments from the returned URL')
default_on = True
preference_section = 'privacy'


def on_result(_request, _search, result):
    if 'parsed_url' not in result:
        return True

    query = result['parsed_url'].query

    if query == "":
        return True
    parsed_query = parse_qsl(query)

    changes = 0
    for i, (param_name, _) in enumerate(list(parsed_query)):
        for reg in regexes:
            if reg.match(param_name):
                parsed_query.pop(i - changes)
                changes += 1
                result['parsed_url'] = result['parsed_url']._replace(query=urlencode(parsed_query))
                result['url'] = urlunparse(result['parsed_url'])
                break

    return True
