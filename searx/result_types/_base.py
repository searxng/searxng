# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=too-few-public-methods, missing-module-docstring
"""Basic types for the typification of results.

- :py:obj:`Result` base class
- :py:obj:`LegacyResult` for internal use only

----

.. autoclass:: Result
   :members:

.. _LegacyResult:

.. autoclass:: LegacyResult
   :members:
"""


from __future__ import annotations

__all__ = ["Result"]

import re
import urllib.parse
import warnings
import typing
import time
import datetime

from collections.abc import Callable

import msgspec

from searx import logger as log

WHITESPACE_REGEX = re.compile('( |\t|\n)+', re.M | re.U)
UNKNOWN = object()


def _normalize_url_fields(result: Result | LegacyResult):

    # As soon we need LegacyResult not any longer, we can move this function to
    # method Result.normalize_result_fields

    if result.url and not result.parsed_url:
        if not isinstance(result.url, str):
            log.debug('result: invalid URL: %s', str(result))
            result.url = ""
            result.parsed_url = None
        else:
            result.parsed_url = urllib.parse.urlparse(result.url)

    if result.parsed_url:
        result.parsed_url = result.parsed_url._replace(
            # if the result has no scheme, use http as default
            scheme=result.parsed_url.scheme or "http",
            path=result.parsed_url.path,
        )
        result.url = result.parsed_url.geturl()

    if isinstance(result, LegacyResult) and getattr(result, "infobox", None):
        # As soon we have InfoboxResult, we can move this function to method
        # InfoboxResult.normalize_result_fields

        infobox_urls: list[dict[str, str]] = getattr(result, "urls", [])
        for item in infobox_urls:
            _url = item.get("url")
            if not _url:
                continue
            _url = urllib.parse.urlparse(_url)
            item["url"] = _url._replace(
                scheme=_url.scheme or "http",
                # netloc=_url.netloc.replace("www.", ""),
                path=_url.path,
            ).geturl()

        infobox_id = getattr(result, "id", None)
        if infobox_id:
            _url = urllib.parse.urlparse(infobox_id)
            result.id = _url._replace(
                scheme=_url.scheme or "http",
                # netloc=_url.netloc.replace("www.", ""),
                path=_url.path,
            ).geturl()


def _normalize_text_fields(result: MainResult | LegacyResult):

    # As soon we need LegacyResult not any longer, we can move this function to
    # method MainResult.normalize_result_fields

    # Actually, a type check should not be necessary if the engine is
    # implemented correctly. Historically, however, we have always had a type
    # check here.

    if result.title and not isinstance(result.title, str):
        log.debug("result: invalid type of field 'title': %s", str(result))
        result.title = str(result)
    if result.content and not isinstance(result.content, str):
        log.debug("result: invalid type of field 'content': %s", str(result))
        result.content = str(result)

    # normalize title and content
    if result.title:
        result.title = WHITESPACE_REGEX.sub(" ", result.title).strip()
    if result.content:
        result.content = WHITESPACE_REGEX.sub(" ", result.content).strip()
    if result.content == result.title:
        # avoid duplicate content between the content and title fields
        result.content = ""


def _filter_urls(result: Result | LegacyResult, filter_func: Callable[[Result | LegacyResult, str, str], str | bool]):
    # pylint: disable=too-many-branches, too-many-statements

    # As soon we need LegacyResult not any longer, we can move this function to
    # method Result.

    url_fields = ["url", "iframe_src", "audio_src", "img_src", "thumbnail_src", "thumbnail"]

    for field_name in url_fields:
        url_src = getattr(result, field_name, "")
        if not url_src:
            continue

        new_url = filter_func(result, field_name, url_src)
        # log.debug("filter_urls: filter_func(result, %s) '%s' -> '%s'", field_name, field_value, new_url)
        if isinstance(new_url, bool):
            if new_url:
                # log.debug("filter_urls: unchanged field %s URL %s", field_name, field_value)
                continue
            log.debug("filter_urls: drop field %s URL %s", field_name, url_src)
            new_url = None
        else:
            log.debug("filter_urls: modify field %s URL %s -> %s", field_name, url_src, new_url)

        setattr(result, field_name, new_url)
        if field_name == "url":
            # sync parsed_url with new_url
            if not new_url:
                result.parsed_url = None
            elif isinstance(new_url, str):
                result.parsed_url = urllib.parse.urlparse(new_url)

    # "urls": are from infobox
    #
    # As soon we have InfoboxResult, we can move this function to method
    # InfoboxResult.normalize_result_fields

    infobox_urls: list[dict[str, str]] = getattr(result, "urls", [])

    if infobox_urls:
        # log.debug("filter_urls: infobox_urls .. %s", infobox_urls)
        new_infobox_urls: list[dict[str, str]] = []

        for item in infobox_urls:
            url_src = item.get("url")
            if not url_src:
                new_infobox_urls.append(item)
                continue

            new_url = filter_func(result, "infobox_urls", url_src)
            if isinstance(new_url, bool):
                if new_url:
                    new_infobox_urls.append(item)
                    # log.debug("filter_urls: leave URL in field 'urls' ('infobox_urls') unchanged -> %s", _url)
                    continue
                log.debug("filter_urls: remove URL from field 'urls' ('infobox_urls') URL %s", url_src)
                new_url = None
            if new_url:
                log.debug("filter_urls: modify URL from field 'urls' ('infobox_urls') URL %s -> %s", url_src, new_url)
                item["url"] = new_url
                new_infobox_urls.append(item)

        setattr(result, "urls", new_infobox_urls)

    # "attributes": are from infobox
    #
    # The infobox has additional subsections for attributes, urls and relatedTopics:

    infobox_attributes: list[dict[str, dict]] = getattr(result, "attributes", [])

    if infobox_attributes:
        # log.debug("filter_urls: infobox_attributes .. %s", infobox_attributes)
        new_infobox_attributes: list[dict[str, dict]] = []

        for item in infobox_attributes:
            image = item.get("image", {})
            url_src = image.get("src", "")
            if not url_src:
                new_infobox_attributes.append(item)
                continue

            new_url = filter_func(result, "infobox_attributes", url_src)
            if isinstance(new_url, bool):
                if new_url:
                    new_infobox_attributes.append(item)
                    # log.debug("filter_urls: leave URL in field 'image.src' unchanged -> %s", url_src)
                    continue
                log.debug("filter_urls: drop field 'image.src' ('infobox_attributes') URL %s", url_src)
                new_url = None

            if new_url:
                log.debug(
                    "filter_urls: modify 'image.src' ('infobox_attributes') URL %s -> %s",
                    url_src,
                    new_url,
                )
                item["image"]["src"] = new_url
                new_infobox_attributes.append(item)

        setattr(result, "attributes", new_infobox_attributes)

    result.normalize_result_fields()


def _normalize_date_fields(result: MainResult | LegacyResult):

    if result.publishedDate:  # do not try to get a date from an empty string or a None type
        try:  # test if publishedDate >= 1900 (datetime module bug)
            result.pubdate = result.publishedDate.strftime('%Y-%m-%d %H:%M:%S%z')
        except ValueError:
            result.publishedDate = None


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
        """Normalize fields ``url`` and ``parse_sql``.

        - If field ``url`` is set and field ``parse_url`` is unset, init
          ``parse_url`` from field ``url``.  The ``url`` field is initialized
          with the resulting value in ``parse_url``, if ``url`` and
          ``parse_url`` are not equal.
        """
        _normalize_url_fields(self)

    def __post_init__(self):
        pass

    def filter_urls(self, filter_func: Callable[[Result | LegacyResult, str, str], str | bool]):
        """A filter function is passed in the ``filter_func`` argument to
        filter and/or modify the URLs.

        The filter function receives the :py:obj:`result object <Result>` as
        the first argument and the field name (``str``) in the second argument.
        In the third argument the URL string value is passed to the filter function.

        The filter function is applied to all fields that contain a URL,
        in addition to the familiar ``url`` field, these include fields such as::

             ["url", "iframe_src", "audio_src", "img_src", "thumbnail_src", "thumbnail"]

        and the ``urls`` list of items of the infobox.

        For each field, the filter function is called and returns a bool or a
        string value:

        - ``True``: leave URL in field unchanged
        - ``False``: remove URL field from result (or remove entire result)
        - ``str``: modified URL to be used instead

        See :ref:`filter urls example`.

        """
        _filter_urls(self, filter_func=filter_func)

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

    def defaults_from(self, other: Result):
        """Fields not set in *self* will be updated from the field values of the
        *other*.
        """
        for field_name in self.__struct_fields__:
            self_val = getattr(self, field_name, False)
            other_val = getattr(other, field_name, False)
            if self_val:
                setattr(self, field_name, other_val)


class MainResult(Result):  # pylint: disable=missing-class-docstring
    """Base class of all result types displayed in :ref:`area main results`."""

    title: str = ""
    """Link title of the result item."""

    content: str = ""
    """Extract or description of the result item"""

    img_src: str = ""
    """URL of a image that is displayed in the result item."""

    thumbnail: str = ""
    """URL of a thumbnail that is displayed in the result item."""

    publishedDate: datetime.datetime | None = None
    """The date on which the object was published."""

    pubdate: str = ""
    """String representation of :py:obj:`MainResult.publishedDate`"""

    length: time.struct_time | None = None
    """Playing duration in seconds."""

    views: str = ""
    """View count in humanized number format."""

    author: str = ""
    """Author of the title."""

    metadata: str = ""
    """Miscellaneous metadata."""

    priority: typing.Literal["", "high", "low"] = ""
    """The priority can be set via :ref:`hostnames plugin`, for example."""

    engines: set[str] = set()
    """In a merged results list, the names of the engines that found this result
    are listed in this field."""

    # open_group and close_group should not manged in the Result
    # class (we should drop it from here!)
    open_group: bool = False
    close_group: bool = False
    positions: list[int] = []
    score: float = 0
    category: str = ""

    def __hash__(self) -> int:
        """Ordinary url-results are equal if their values for
        :py:obj:`Result.template`, :py:obj:`Result.parsed_url` (without scheme)
        and :py:obj:`MainResult.img_src` are equal.
        """
        if not self.parsed_url:
            raise ValueError(f"missing a value in field 'parsed_url': {self}")

        url = self.parsed_url
        return hash(
            f"{self.template}"
            + f"|{url.netloc}|{url.path}|{url.params}|{url.query}|{url.fragment}"
            + f"|{self.img_src}"
        )

    def normalize_result_fields(self):
        super().normalize_result_fields()
        _normalize_text_fields(self)
        _normalize_date_fields(self)
        if self.engine:
            self.engines.add(self.engine)


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

    # emulate field types from type class Result
    url: str | None
    template: str
    engine: str
    parsed_url: urllib.parse.ParseResult | None

    # emulate field types from type class MainResult
    title: str
    content: str
    img_src: str
    thumbnail: str
    priority: typing.Literal["", "high", "low"]
    engines: set[str]
    positions: list[int]
    score: float
    category: str
    publishedDate: datetime.datetime | None = None
    pubdate: str = ""

    # infobox result
    urls: list[dict[str, str]]
    attributes: list[dict[str, str]]

    def as_dict(self):
        return self

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # emulate field types from type class Result
        self["url"] = self.get("url")
        self["template"] = self.get("template", "default.html")
        self["engine"] = self.get("engine", "")
        self["parsed_url"] = self.get("parsed_url")

        # emulate field types from type class MainResult
        self["title"] = self.get("title", "")
        self["content"] = self.get("content", "")
        self["img_src"] = self.get("img_src", "")
        self["thumbnail"] = self.get("thumbnail", "")
        self["priority"] = self.get("priority", "")
        self["engines"] = self.get("engines", set())
        self["positions"] = self.get("positions", "")
        self["score"] = self.get("score", 0)
        self["category"] = self.get("category", "")

        if "infobox" in self:
            self["urls"] = self.get("urls", [])
            self["attributes"] = self.get("attributes", [])

        # Legacy types that have already been ported to a type ..

        if "answer" in self:
            warnings.warn(
                f"engine {self.engine} is using deprecated `dict` for answers"
                f" / use a class from searx.result_types.answer",
                DeprecationWarning,
            )
            self.template = "answer/legacy.html"

        if self.template == "keyvalue.html":
            warnings.warn(
                f"engine {self.engine} is using deprecated `dict` for key/value results"
                f" / use a class from searx.result_types",
                DeprecationWarning,
            )

    def __getattr__(self, name: str, default=UNSET) -> typing.Any:
        if default == self.UNSET and name not in self:
            raise AttributeError(f"LegacyResult object has no field named: {name}")
        return self[name]

    def __setattr__(self, name: str, val):
        self[name] = val

    def __hash__(self) -> int:  # type: ignore

        if "answer" in self:
            # deprecated ..
            return hash(self["answer"])

        if self.template == "images.html":
            # image results are equal if their values for template, the url and
            # the img_src are equal.
            return hash(f"{self.template}|{self.url}|{self.img_src}")

        if not any(cls in self for cls in ["suggestion", "correction", "infobox", "number_of_results", "engine_data"]):
            # Ordinary url-results are equal if their values for template,
            # parsed_url (without schema) and img_src` are equal.

            # Code copied from with MainResult.__hash__:
            if not self.parsed_url:
                raise ValueError(f"missing a value in field 'parsed_url': {self}")

            url = self.parsed_url
            return hash(
                f"{self.template}"
                + f"|{url.netloc}|{url.path}|{url.params}|{url.query}|{url.fragment}"
                + f"|{self.img_src}"
            )

        return id(self)

    def __eq__(self, other):

        return hash(self) == hash(other)

    def __repr__(self) -> str:

        return f"LegacyResult: {super().__repr__()}"

    def normalize_result_fields(self):
        _normalize_date_fields(self)
        _normalize_url_fields(self)
        _normalize_text_fields(self)
        if self.engine:
            self.engines.add(self.engine)

    def defaults_from(self, other: LegacyResult):
        for k, v in other.items():
            if not self.get(k):
                self[k] = v

    def filter_urls(self, filter_func: Callable[[Result | LegacyResult, str, str], str | bool]):
        """See :py:obj:`Result.filter_urls`"""
        _filter_urls(self, filter_func=filter_func)
