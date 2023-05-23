# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
""".. _botdetection src:

Bot detection methods
---------------------

The methods implemented in this python package are use by the :ref:`limiter src`.

"""

import flask


def dump_request(request: flask.Request):
    return (
        "%s: '%s'" % (request.headers.get('X-Forwarded-For'), request.path)
        + " || form: %s" % request.form
        + " || Accept: %s" % request.headers.get('Accept')
        + " || Accept-Language: %s" % request.headers.get('Accept-Language')
        + " || Accept-Encoding: %s" % request.headers.get('Accept-Encoding')
        + " || Content-Type: %s" % request.headers.get('Content-Type')
        + " || Content-Length: %s" % request.headers.get('Content-Length')
        + " || Connection: %s" % request.headers.get('Connection')
        + " || User-Agent: %s" % request.headers.get('User-Agent')
    )
