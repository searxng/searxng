'''
searx is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

searx is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with searx. If not, see < http://www.gnu.org/licenses/ >.

(C) 2015 by Adam Tauber, <asciimoo@gmail.com>
'''

from flask_babel import gettext
import re
from urllib.parse import urlunparse, parse_qsl, urlencode

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


def on_result(request, search, result):
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
