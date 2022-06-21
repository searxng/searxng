# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Answer item in the result list.  The answer result item is used in
the :origin:`results.html <searx/templates/simple/results.html>` template.

A answer item is a dictionary type with dedicated keys and values.  In the
result list a answer item is identified by the existence of the key
``suggestion``.

.. code:: python

   results.append({
       'answer' : str,
       'url'    : str,
   })

answer : ``str``
  The answer string append by the engine.

url : ``str``
  A link that is related to the answer (e.g. the origin of the answer)

"""


class Answers(dict):
    """Dictionary of answers in the :py:obj:`.container.ResultContainer`"""

    def add(self, result):
        self[result['answer']] = result
