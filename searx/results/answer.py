# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Answer item in the result list.  The answer result item is used in
the :origin:`results.html <searx/templates/simple/results.html>` template.

A answer item is a dictionary type with dedicated keys and values.

.. code:: python

   results.append({
       'answer' : str,
       'url'    : str,
   })

answer : ``str``
  The answer string append by the engine.

url : ``str``
  A link that is related to the answer (e.g. the origin of the answer).

"""


def is_answer(result):
    """Returns ``True`` if result type is :py:obj:`.answer`, otherwise ``False``

    In the result list a answer item is identified by the existence of the key
    ``answer``.
    """
    return 'answer' in result


class Answers(dict):
    """Dictionary of answers in the :py:obj:`.container.ResultContainer`"""

    def add(self, result):
        self[result['answer']] = result


def answer_modify_url(modify_url_func, result):
    """Modify 'url' field in the answer-result.

    :param func modify_url_func: A function that gets one argument; the 'url'
        field of the ``result`` item.  The function returns the URL to use
        instead (even the URL is not modified).  To drop the 'url' field from
        the result the function returns ``None``.

    :param dict result: The result item.
    """

    if not is_answer(result):
        return

    url = result.get('url')
    if not url:
        return

    _url = modify_url_func(url)
    if _url is None:
        # logger.debug("answer: remove url from %s", url)
        del result['url']
    elif _url != url:
        # logger.debug("answer: redirect url %s", _url)
        result['url'] = _url
