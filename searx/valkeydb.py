# SPDX-License-Identifier: AGPL-3.0-or-later
"""Implementation of the valkey client (valkey-py_).

.. _valkey-py: https://github.com/valkey-io/valkey-py

This implementation uses the :ref:`settings valkey` setup from ``settings.yml``.
A valkey DB connect can be tested by::

  >>> from searx import valkeydb
  >>> valkeydb.initialize()
  True
  >>> db = valkeydb.client()
  >>> db.set("foo", "bar")
  True
  >>> db.get("foo")
  b'bar'
  >>>

"""

import os
import sys
if sys.platform != "win32":
    import pwd
import logging
import warnings

import valkey
from valkey.exceptions import ValkeyError
from searx import get_setting


_CLIENT = None
logger = logging.getLogger(__name__)


def client() -> valkey.Valkey:
    assert _CLIENT is not None
    return _CLIENT


def initialize():
    global _CLIENT  # pylint: disable=global-statement
    if get_setting('redis.url'):
        warnings.warn("setting redis.url is deprecated, use valkey.url", DeprecationWarning)
    valkey_url = get_setting('valkey.url') or get_setting('redis.url')
    if not valkey_url:
        return False
    try:
        # create a client, but no connection is done
        _CLIENT = valkey.Valkey.from_url(valkey_url) # type: ignore

        # log the parameters as seen by the valkey lib, without the password
        kwargs = _CLIENT.get_connection_kwargs().copy()
        kwargs.pop('password', None)
        kwargs = ' '.join([f'{k}={v!r}' for k, v in kwargs.items()])
        logger.info("connecting to Valkey %s", kwargs)

        # check the connection
        _CLIENT.ping()

        # no error: the valkey connection is working
        logger.info("connected to Valkey")
        return True
    except ValkeyError:
        _CLIENT = None
        if not sys.platform == "win32":
            _pw = pwd.getpwuid(os.getuid()) 
            logger.exception("[%s (%s)] can't connect valkey DB ...", _pw.pw_name, _pw.pw_uid)
    return False
