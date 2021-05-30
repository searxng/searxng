# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=missing-function-docstring
"""Redis engine (offline)

"""

import redis  # pylint: disable=import-error

engine_type = 'offline'

# redis connection variables
host = '127.0.0.1'
port = 6379
password = ''
db = 0

# engine specific variables
paging = False
result_template = 'key-value.html'
exact_match_only = True

redis_client = None
def init(_engine_settings):
    # pylint: disable=global-statement
    global redis_client
    redis_client = redis.StrictRedis(
        host = host,
        port = port,
        db = db,
        password = password or None,
        decode_responses = True,
    )

def search(query, _params):

    if not exact_match_only:
        return search_keys(query)

    ret = redis_client.hgetall(query)
    if ret:
        ret['template'] = result_template
        return [ret]

    if ' ' in query:
        qset, rest = query.split(' ', 1)
        ret = []
        for res in redis_client.hscan_iter(
                qset, match='*{}*'.format(rest)
        ):
            ret.append({
                res[0]: res[1],
                'template': result_template,
            })
        return ret
    return []

def search_keys(query):
    ret = []
    for key in redis_client.scan_iter(
            match='*{}*'.format(query)
    ):
        key_type = redis_client.type(key)
        res = None

        if key_type == 'hash':
            res = redis_client.hgetall(key)
        elif key_type == 'list':
            res = dict(enumerate(redis_client.lrange(key, 0, -1)))

        if res:
            res['template'] = result_template
            res['redis_key'] = key
            ret.append(res)
    return ret
