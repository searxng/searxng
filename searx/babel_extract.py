# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""This module implements the :origin:`searxng_msg <babel.cfg>` extractor to
extract messages from:

- :origin:`searx/searxng.msg`

The ``searxng.msg`` files are selected by Babel_, see Babel's configuration in
:origin:`babel.cfg`::

    searxng_msg = searx.babel_extract.extract
    ...
    [searxng_msg: **/searxng.msg]

A ``searxng.msg`` file is a python file that is *executed* by the
:py:obj:`extract` function.  Additional ``searxng.msg`` files can be added by:

1. Adding a ``searxng.msg`` file in one of the SearXNG python packages and
2. implement a method in :py:obj:`extract` that yields messages from this file.

.. _Babel: https://babel.pocoo.org/en/latest/index.html

"""

from os import path

SEARXNG_MSG_FILE = "searxng.msg"
_MSG_FILES = [path.join(path.dirname(__file__), SEARXNG_MSG_FILE)]


def extract(
    # pylint: disable=unused-argument
    fileobj,
    keywords,
    comment_tags,
    options,
):
    """Extract messages from ``searxng.msg`` files by a custom extractor_.

    .. _extractor:
       https://babel.pocoo.org/en/latest/messages.html#writing-extraction-methods
    """
    if fileobj.name not in _MSG_FILES:
        raise RuntimeError("don't know how to extract messages from %s" % fileobj.name)

    namespace = {}
    exec(fileobj.read(), {}, namespace)  # pylint: disable=exec-used

    for name in namespace['__all__']:
        for k, v in namespace[name].items():
            yield 0, '_', v, ["%s['%s']" % (name, k)]
