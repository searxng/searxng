# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=too-few-public-methods, missing-module-docstring
"""Basic types for the typification of results.

- :py:obj:`Result` base class
- :py:obj:`LegacyResult` for internal use only

----

.. autoclass:: Result
   :members:

.. autoclass:: LegacyResult
   :members:
"""


from __future__ import annotations

__all__ = ["Result"]

import re
import urllib.parse
import warnings

import msgspec


class Result(msgspec.Struct, kw_only=True):
    """Base class of all result types :ref:`result types`."""

    url: str | None = None
    """A link related to this *result*"""

    template: str = "default.html"
    """Name of the template used to render the result.

    By default :origin:`result_templates/default.html
    <searx/templates/simple/result_templates/default.html>` is used.
    """

    engine: str | None = ""
    """Name of the engine *this* result comes from.  In case of *plugins* a
    prefix ``plugin:`` is set, in case of *answerer* prefix ``answerer:`` is
    set.

    The field is optional and is initialized from the context if necessary.
    """

    parsed_url: urllib.parse.ParseResult | None = None
    """:py:obj:`urllib.parse.ParseResult` of :py:obj:`Result.url`.

    The field is optional and is initialized from the context if necessary.
    """

    def normalize_result_fields(self):
        """Normalize a result ..

        - if field ``url`` is set and field ``parse_url`` is unset, init
          ``parse_url`` from field ``url``.  This method can be extended in the
          inheritance.

        """

        if not self.parsed_url and self.url:
            self.parsed_url = urllib.parse.urlparse(self.url)

            # if the result has no scheme, use http as default
            if not self.parsed_url.scheme:
                self.parsed_url = self.parsed_url._replace(scheme="http")
                self.url = self.parsed_url.geturl()

    def __post_init__(self):
        pass

    def __hash__(self) -> int:
        """Generates a hash value that uniquely identifies the content of *this*
        result.  The method can be adapted in the inheritance to compare results
        from different sources.

        If two result objects are not identical but have the same content, their
        hash values should also be identical.

        The hash value is used in contexts, e.g. when checking for equality to
        identify identical results from different sources (engines).
        """

        return id(self)

    def __eq__(self, other):
        """py:obj:`Result` objects are equal if the hash values of the two
        objects are equal.  If needed, its recommended to overwrite
        "py:obj:`Result.__hash__`."""

        return hash(self) == hash(other)

    # for legacy code where a result is treated as a Python dict

    def __setitem__(self, field_name, value):

        return setattr(self, field_name, value)

    def __getitem__(self, field_name):

        if field_name not in self.__struct_fields__:
            raise KeyError(f"{field_name}")
        return getattr(self, field_name)

    def __iter__(self):

        return iter(self.__struct_fields__)

    def as_dict(self):
        return {f: getattr(self, f) for f in self.__struct_fields__}


class MainResult(Result):  # pylint: disable=missing-class-docstring

    # open_group and close_group should not manged in the Result class (we should rop it from here!)
    open_group: bool = False
    close_group: bool = False

    title: str = ""
    """Link title of the result item."""

    content: str = ""
    """Extract or description of the result item"""

    img_src: str = ""
    """URL of a image that is displayed in the result item."""

    thumbnail: str = ""
    """URL of a thumbnail that is displayed in the result item."""


class LegacyResult(dict):
    """A wrapper around a legacy result item.  The SearXNG core uses this class
    for untyped dictionaries / to be downward compatible.

    This class is needed until we have implemented an :py:obj:`Result` class for
    each result type and the old usages in the codebase have been fully
    migrated.

    There is only one place where this class is used, in the
    :py:obj:`searx.results.ResultContainer`.

    .. attention::

       Do not use this class in your own implementations!
    """

    UNSET = object()
    WHITESPACE_REGEX = re.compile('( |\t|\n)+', re.M | re.U)

    def as_dict(self):
        return self

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Init fields with defaults / compare with defaults of the fields in class Result
        self.engine = self.get("engine", "")
        self.template = self.get("template", "default.html")
        self.url = self.get("url", None)
        self.parsed_url = self.get("parsed_url", None)

        self.content = self.get("content", "")
        self.title = self.get("title", "")

        # Legacy types that have already been ported to a type ..

        if "answer" in self:
            warnings.warn(
                f"engine {self.engine} is using deprecated `dict` for answers"
                f" / use a class from searx.result_types.answer",
                DeprecationWarning,
            )
            self.template = "answer/legacy.html"

    def __hash__(self) -> int:  # type: ignore

        if "answer" in self:
            return hash(self["answer"])
        if not any(cls in self for cls in ["suggestion", "correction", "infobox", "number_of_results", "engine_data"]):
            # it is a commun url-result ..
            return hash(self.url)
        return id(self)

    def __eq__(self, other):

        return hash(self) == hash(other)

    def __repr__(self) -> str:

        return f"LegacyResult: {super().__repr__()}"

    def __getattr__(self, name: str, default=UNSET):

        if default == self.UNSET and name not in self:
            raise AttributeError(f"LegacyResult object has no field named: {name}")
        return self[name]

    def __setattr__(self, name: str, val):

        self[name] = val

    def normalize_result_fields(self):

        self.title = self.WHITESPACE_REGEX.sub(" ", self.title)

        if not self.parsed_url and self.url:
            self.parsed_url = urllib.parse.urlparse(self.url)

            # if the result has no scheme, use http as default
            if not self.parsed_url.scheme:
                self.parsed_url = self.parsed_url._replace(scheme="http")
                self.url = self.parsed_url.geturl()

        if self.content:
            self.content = self.WHITESPACE_REGEX.sub(" ", self.content)
            if self.content == self.title:
                # avoid duplicate content between the content and title fields
                self.content = ""
