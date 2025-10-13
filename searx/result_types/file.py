# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Typification of the *file* results.  Results of this type are rendered in
the :origin:`file.html <searx/templates/simple/result_templates/file.html>`
template.

----

.. autoclass:: File
   :members:
   :show-inheritance:

"""
# pylint: disable=too-few-public-methods


__all__ = ["File"]

import typing as t
import mimetypes

from ._base import MainResult


@t.final
class File(MainResult, kw_only=True):
    """Class for results of type *file*"""

    template: str = "file.html"

    filename: str = ""
    """Name of the file."""

    size: str = ""
    """Size of bytes in human readable notation (``MB`` for 1024 * 1024 Bytes
    file size.)"""

    time: str = ""
    """Indication of a time, such as the date of the last modification or the
    date of creation. This is a simple string, the *date* of which can be freely
    chosen according to the context."""

    mimetype: str = ""
    """Mimetype/Subtype of the file.  For ``audio`` and ``video``, a URL can be
    passed in the :py:obj:`File.embedded` field to embed the referenced media in
    the result.  If no value is specified, the MIME type is determined from
    ``self.filename`` or, alternatively, from ``self.embedded`` (if either of
    the two values is set)."""

    abstract: str = ""
    """Abstract of the file."""

    author: str = ""
    """Author of the file."""

    embedded: str = ""
    """URL of an embedded media type (audio or video) / is collapsible."""

    mtype: str = ""
    """Used for displaying :py:obj:`File.embedded`.  Its value is automatically
    populated from the base type of :py:obj:`File.mimetype`, and can be
    explicitly set to enforce e.g. ``audio`` or ``video`` when mimetype is
    something like "application/ogg" but its know the content is for example a
    video."""

    subtype: str = ""
    """Used for displaying :py:obj:`File.embedded`.  Its value is automatically
    populated from the subtype type of :py:obj:`File.mimetype`, and can be
    explicitly set to enforce a subtype for the :py:obj:`File.embedded`
    element."""

    def __post_init__(self):
        super().__post_init__()

        if not self.mtype or not self.subtype:

            fn = self.filename or self.embedded
            if not self.mimetype and fn:
                self.mimetype = mimetypes.guess_type(fn, strict=False)[0] or ""

            mtype, subtype = (self.mimetype.split("/", 1) + [""])[:2]

            if not self.mtype:
                # I don't know why, but the ogg video stream is not displayed,
                # may https://github.com/videojs/video.js can help?
                if self.embedded.endswith(".ogv"):
                    self.mtype = "video"
                elif self.embedded.endswith(".oga"):
                    self.mtype = "audio"
                else:
                    self.mtype = mtype

            if not self.subtype:
                self.subtype = subtype
