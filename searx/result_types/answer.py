# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Typification of the *answer* results.  Results of this type are rendered in
the :origin:`answers.html <searx/templates/simple/elements/answers.html>`
template.

----

.. autoclass:: BaseAnswer
   :members:
   :show-inheritance:

.. autoclass:: Answer
   :members:
   :show-inheritance:

.. autoclass:: Translations
   :members:
   :show-inheritance:

.. autoclass:: AnswerSet
   :members:
   :show-inheritance:
"""
# pylint: disable=too-few-public-methods

from __future__ import annotations

__all__ = ["AnswerSet", "Answer", "Translations"]

import msgspec

from ._base import Result


class BaseAnswer(Result, kw_only=True):
    """Base class of all answer types.  It is not intended to build instances of
    this class (aka *abstract*)."""


class AnswerSet:
    """Aggregator for :py:obj:`BaseAnswer` items in a result container."""

    def __init__(self):
        self._answerlist = []

    def __len__(self):
        return len(self._answerlist)

    def __bool__(self):
        return bool(self._answerlist)

    def add(self, answer: BaseAnswer) -> None:
        a_hash = hash(answer)
        for i in self._answerlist:
            if hash(i) == a_hash:
                return
        self._answerlist.append(answer)

    def __iter__(self):
        """Sort items in this set and iterate over the items."""
        self._answerlist.sort(key=lambda answer: answer.template)
        yield from self._answerlist

    def __contains__(self, answer: BaseAnswer) -> bool:
        a_hash = hash(answer)
        for i in self._answerlist:
            if hash(i) == a_hash:
                return True
        return False


class Answer(BaseAnswer, kw_only=True):
    """Simple answer type where the *answer* is a simple string with an optional
    :py:obj:`url field <Result.url>` field to link a resource (article, map, ..)
    related to the answer."""

    template: str = "answer/legacy.html"

    answer: str
    """Text of the answer."""

    def __hash__(self):
        """The hash value of field *answer* is the hash value of the
        :py:obj:`Answer` object.  :py:obj:`Answer <Result.__eq__>` objects are
        equal, when the hash values of both objects are equal."""
        return hash(self.answer)


class Translations(BaseAnswer, kw_only=True):
    """Answer type with a list of translations.

    The items in the list of :py:obj:`Translations.translations` are of type
    :py:obj:`Translations.Item`:

    .. code:: python

       def response(resp):
           results = []
           ...
           foo_1 = Translations.Item(
               text="foobar",
               synonyms=["bar", "foo"],
               examples=["foo and bar are placeholders"],
           )
           foo_url="https://www.deepl.com/de/translator#en/de/foo"
           ...
           Translations(results=results, translations=[foo], url=foo_url)

    """

    template: str = "answer/translations.html"
    """The template in :origin:`answer/translations.html
    <searx/templates/simple/answer/translations.html>`"""

    translations: list[Translations.Item]
    """List of translations."""

    def __post_init__(self):
        if not self.translations:
            raise ValueError("Translation does not have an item in the list translations")

    class Item(msgspec.Struct, kw_only=True):
        """A single element of the translations / a translation.  A translation
        consists of at least a mandatory ``text`` property (the translation) ,
        optional properties such as *definitions*, *synonyms* and *examples* are
        possible."""

        text: str
        """Translated text."""

        transliteration: str = ""
        """Transliteration_ of the requested translation.

        .. _Transliteration: https://en.wikipedia.org/wiki/Transliteration
        """

        examples: list[str] = []
        """List of examples for the requested translation."""

        definitions: list[str] = []
        """List of definitions for the requested translation."""

        synonyms: list[str] = []
        """List of synonyms for the requested translation."""
