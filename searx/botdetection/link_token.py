# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""
Method ``link_token``
---------------------

The ``link_token`` method evaluates a request as :py:obj:`suspicious
<is_suspicious>` if the URL ``/client<token>.css`` is not requested by the
client.  By adding a random component (the token) in the URL a bot can not send
a ping by request a static URL.

.. note::

   This method requires a redis DB and needs a HTTP X-Forwarded-For_ header.

To get in use of this method a flask URL route needs to be added:

.. code:: python

   @app.route('/client<token>.css', methods=['GET', 'POST'])
   def client_token(token=None):
       link_token.ping(request, token)
       return Response('', mimetype='text/css')

And in the HTML template from flask a stylesheet link is needed (the value of
``link_token`` comes from :py:obj:`get_token`):

.. code:: html

   <link rel="stylesheet"
         href="{{ url_for('client_token', token=link_token) }}"
         type="text/css" />

.. _X-Forwarded-For:
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Forwarded-For

"""

import string
import random
import flask

from searx import logger
from searx import redisdb
from searx.redislib import secret_hash

TOKEN_LIVE_TIME = 600
"""Livetime (sec) of limiter's CSS token."""

PING_KEY = 'SearXNG_limiter.ping'
TOKEN_KEY = 'SearXNG_limiter.token'

logger = logger.getChild('botdetection.link_token')


def is_suspicious(request: flask.Request):
    """Checks if there is a valid ping for this request, if not this request is
    rated as *suspicious*"""
    redis_client = redisdb.client()
    if not redis_client:
        return False

    ping_key = get_ping_key(request)
    if not redis_client.get(ping_key):
        logger.warning(
            "missing ping (IP: %s) / request: %s",
            request.headers.get('X-Forwarded-For', ''),
            ping_key,
        )
        return True

    logger.debug("found ping for this request: %s", ping_key)
    return False


def ping(request: flask.Request, token: str):
    """This function is called by a request to URL ``/client<token>.css``"""
    redis_client = redisdb.client()
    if not redis_client:
        return
    if not token_is_valid(token):
        return
    ping_key = get_ping_key(request)
    logger.debug("store ping for: %s", ping_key)
    redis_client.set(ping_key, 1, ex=TOKEN_LIVE_TIME)


def get_ping_key(request: flask.Request):
    """Generates a hashed key that fits (more or less) to a request.  At least
    X-Forwarded-For_ is needed to be able to assign the request to an IP.

    """
    return secret_hash(
        PING_KEY
        + request.headers.get('X-Forwarded-For', '')
        + request.headers.get('Accept-Language', '')
        + request.headers.get('User-Agent', '')
    )


def token_is_valid(token) -> bool:
    valid = token == get_token()
    logger.debug("token is valid --> %s", valid)
    return valid


def get_token() -> str:
    """Returns current token.  If there is no currently active token a new token
    is generated randomly and stored in the redis DB.

    - :py:obj:`TOKEN_LIVE_TIME`
    - :py:obj:`TOKEN_KEY`

    """
    redis_client = redisdb.client()
    if not redis_client:
        # This function is also called when limiter is inactive / no redis DB
        # (see render function in webapp.py)
        return '12345678'
    token = redis_client.get(TOKEN_KEY)
    if token:
        token = token.decode('UTF-8')
    else:
        token = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(16))
        redis_client.set(TOKEN_KEY, token, ex=TOKEN_LIVE_TIME)
    return token
