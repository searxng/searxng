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

name = gettext('Self Informations')
description = gettext('Displays your IP if the query is "ip" and your user agent if the query contains "user agent".')
default_on = True
preference_section = 'query'
query_keywords = ['user-agent']
query_examples = ''

# Self User Agent regex
p = re.compile('.*user[ -]agent.*', re.IGNORECASE)


# attach callback to the post search hook
#  request: flask request object
#  ctx: the whole local context of the pre search hook
def post_search(request, search):
    if search.search_query.pageno > 1:
        return True
    if search.search_query.query == 'ip':
        x_forwarded_for = request.headers.getlist("X-Forwarded-For")
        if x_forwarded_for:
            ip = x_forwarded_for[0]
        else:
            ip = request.remote_addr
        search.result_container.answers['ip'] = {'answer': ip}
    elif p.match(search.search_query.query):
        ua = request.user_agent
        search.result_container.answers['user-agent'] = {'answer': ua}
    return True
