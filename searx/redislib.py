# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""A collection of convenient functions and redis/lua scripts.
"""

import hmac

from searx import get_setting


def secret_hash(name: str):
    """Creates a hash of the ``name``.

    Combines argument ``name`` with the ``secret_key`` from :ref:`settings
    server`.  This function can be used to get a more anonymized name of a Redis
    KEY.

    :param name: the name to create a secret hash for
    :type name: str
    """
    m = hmac.new(bytes(name, encoding='utf-8'), digestmod='sha256')
    m.update(bytes(get_setting('server.secret_key'), encoding='utf-8'))
    return m.hexdigest()
