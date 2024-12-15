# SPDX-License-Identifier: AGPL-3.0-or-later
"""The *answerers* give instant answers related to the search query, they
usually provide answers of type :py:obj:`Answer <searx.result_types.Answer>`.

Here is an example of a very simple answerer that adds a "Hello" into the answer
area:

.. code::

   from flask_babel import gettext as _
   from searx.answerers import Answerer
   from searx.result_types import Answer

   class MyAnswerer(Answerer):

       keywords = [ "hello", "hello world" ]

       def info(self):
           return AnswererInfo(name=_("Hello"), description=_("lorem .."), keywords=self.keywords)

       def answer(self, request, search):
           return [ Answer(answer="Hello") ]

----

.. autoclass:: Answerer
   :members:

.. autoclass:: AnswererInfo
   :members:

.. autoclass:: AnswerStorage
   :members:

.. autoclass:: searx.answerers._core.ModuleAnswerer
   :members:
   :show-inheritance:

"""

from __future__ import annotations

__all__ = ["AnswererInfo", "Answerer", "AnswerStorage"]


from ._core import AnswererInfo, Answerer, AnswerStorage

STORAGE: AnswerStorage = AnswerStorage()
STORAGE.load_builtins()
