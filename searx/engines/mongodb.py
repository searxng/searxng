# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""MongoDB engine (Offline)

"""

import re
from pymongo import MongoClient  # pylint: disable=import-error

engine_type = 'offline'

# mongodb connection variables
host = '127.0.0.1'
port = 27017
username = ''
password = ''
database = None
collection = None
key = None

# engine specific variables
paging = True
results_per_page = 20
exact_match_only = False
result_template = 'key-value.html'

_client = None


def init(_):
    connect()


def connect():
    global _client  # pylint: disable=global-statement
    kwargs = {'port': port}
    if username:
        kwargs['username'] = username
    if password:
        kwargs['password'] = password
    _client = MongoClient(host, **kwargs)[database][collection]


def search(query, params):
    results = []
    if exact_match_only:
        q = {'$eq': query}
    else:
        _re = re.compile('.*{0}.*'.format(re.escape(query)), re.I | re.M)
        q = {'$regex': _re}

    query = _client.find({key: q}).skip((params['pageno'] - 1) * results_per_page).limit(results_per_page)

    results.append({'number_of_results': query.count()})
    for r in query:
        del r['_id']
        r = {str(k): str(v) for k, v in r.items()}
        r['template'] = result_template
        results.append(r)

    return results
