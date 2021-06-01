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
(C) 2018, 2020 by Vaclav Zouzalik
'''

from flask_babel import gettext
import hashlib
import re

name = "Hash plugin"
description = gettext("Converts strings to different hash digests.")
default_on = True
preference_section = 'query'
query_keywords = ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']
query_examples = 'sha512 The quick brown fox jumps over the lazy dog'

parser_re = re.compile('(md5|sha1|sha224|sha256|sha384|sha512) (.*)', re.I)


def post_search(request, search):
    # process only on first page
    if search.search_query.pageno > 1:
        return True
    m = parser_re.match(search.search_query.query)
    if not m:
        # wrong query
        return True

    function, string = m.groups()
    if string.strip().__len__() == 0:
        # end if the string is empty
        return True

    # select hash function
    f = hashlib.new(function.lower())

    # make digest from the given string
    f.update(string.encode('utf-8').strip())
    answer = function + " " + gettext('hash digest') + ": " + f.hexdigest()

    # print result
    search.result_container.answers.clear()
    search.result_container.answers['hash'] = {'answer': answer}
    return True
