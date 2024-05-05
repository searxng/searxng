# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,invalid-name

import re
from flask_babel import gettext


name = gettext('Self Information')
description = gettext('Displays your IP if the query is "ip" and your user agent if the query contains "user agent".')
default_on = True
preference_section = 'query'
query_keywords = ['user-agent']
query_examples = ''

# Self User Agent regex
p = re.compile('.*user[ -]agent.*', re.IGNORECASE)


def get_client_ip(request):
    botdetection_context = getattr(request, "botdetection_context", None)
    if botdetection_context:
        return request.botdetection_request_info.real_ip
    return request.remote_addr


def post_search(request, search):
    if search.search_query.pageno > 1:
        return True
    if search.search_query.query == 'ip':
        ip = get_client_ip(request)
        search.result_container.answers['ip'] = {'answer': ip}
    elif p.match(search.search_query.query):
        ua = request.user_agent
        search.result_container.answers['user-agent'] = {'answer': ua}
    return True
