# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Correction item in the result list.  The correction result item is used in
the :origin:`results.html <searx/templates/simple/results.html>` template.

A correction item is a dictionary type with dedicated keys and values.

.. code:: python

   results.append({
       'correction' : str,
   })

The context ``corrections`` of the HTML template is a set of dictionaries:

.. code:: python

   corrections = [
       {
           'url'   : str,
           'title' : str,
       },
       {...},
       ...
   ]

url : ``str``
  The SearXNG search URL for the correction term.

title : ``str``
  The 'correction' string append by the engine.

"""


def is_correction(result):
    """Returns ``True`` if result type is :py:obj:`.correction`, otherwise
    ``False``

    In the result list a answer item is identified by the existence of the key
    ``correction``.
    """
    return 'correction' in result


class Corrections(set):
    """Set of corrections in the :py:obj:`.container.ResultContainer`"""
