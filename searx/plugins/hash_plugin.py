# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

import hashlib
import re

from flask_babel import gettext

name = "Hash plugin"
description = gettext("Converts strings to different hash digests.")
default_on = True
preference_section = 'query'
query_keywords = ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']
query_examples = 'sha512 The quick brown fox jumps over the lazy dog'

parser_re = re.compile('(md5|sha1|sha224|sha256|sha384|sha512) (.*)', re.I)


def post_search(_request, search):
    # process only on first page
    if search.search_query.pageno > 1:
        return True
    m = parser_re.match(search.search_query.query)
    if not m:
        # wrong query
        return True

    function, string = m.groups()
    if not string.strip():
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
