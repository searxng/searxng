# SPDX-License-Identifier: AGPL-3.0-or-later
"""Typification of the *image* results.  Results of this type are rendered in
the :origin:`images.html <searx/templates/simple/result_templates/images.html>`
template.

.. autoclass:: Image
   :members:
   :show-inheritance:

.. autoclass:: ImageRef
   :members:

"""
# pylint: disable=too-few-public-methods
__all__ = ["Image", "ImageRef"]

import mimetypes
import types
import typing as t
from collections.abc import Callable

import msgspec

from ._base import MainResult, Result, log, LegacyResult

MimeSubType = t.Literal["png", "svg+xml", "jpeg", "bmp", "x-icon", "tiff"]

MIMESUB: dict[MimeSubType, str] = {
    "png": "PNG",
    "svg+xml": "SVG",
    "jpeg": "JPG",
    "bmp": "BMP",
    "x-icon": "ICO",
    "tiff": "TIF",
}


class ImageRef(msgspec.Struct, kw_only=True):
    """Reference to an (alternative) image format"""

    url: str
    """URL of the image reference."""

    subtype: MimeSubType
    """Subtype (mimetype) of the image format."""

    label: str = ""
    """Label of the reference, default is build from the uppercase of
    :py:obj:`Image.ImageRef.subtype`."""

    mtype: t.Literal["image"] = "image"

    def __post_init__(self):
        if not self.label:
            self.label = MIMESUB.get(self.subtype, self.subtype.upper())


@t.final
class Image(MainResult, kw_only=True):
    """Result type suitable for displaying images.

    The images are displayed as small thumbnails in the main results list.
    Clicking on the preview opens a gallery view in which all further metadata
    for the image is displayed."""

    template: str = "images.html"

    thumbnail_src: str = ""
    """URL of a preview of the image."""

    resolution: str = ""
    """The resolution of the image (e.g. ``1920 x 1080`` pixel)"""

    img_format: str = ""
    """The format of the image :py:obj:`.MainResult.img_src` (e.g. ``png``)."""

    source: str = ""
    """Source of the image."""

    filesize: str = ""
    """Size of bytes in :py:obj:`human readable <searx.humanize_bytes>` notation
    (e.g. ``1MB`` for ``1024*1024`` Bytes filesize)."""

    formats: list[ImageRef] = []
    """List of links to alternative image formats."""

    def __post_init__(self):
        super().__post_init__()

        if not self.img_format:
            # automatically guess the image format based on the path of the image
            mimetype = mimetypes.guess_type(self.img_src)[0]
            if mimetype:
                subtype = mimetype.split("/")[-1]
                if subtype in MIMESUB:
                    self.img_format = MIMESUB[subtype]
                else:
                    self.img_format = subtype.upper()

    def filter_urls(self, filter_func: "Callable[[Result | LegacyResult, str, str], str | bool ]"):

        for _ref in self.formats[:]:
            _name = f"Image.formats:{_ref.label}"
            try:
                _url = filter_func(self, _name, _ref.url)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                # pylint: disable=no-member
                _tb: types.TracebackType = exc.__traceback__.tb_next.tb_next  # type: ignore
                _fn = _tb.tb_frame.f_code.co_filename
                _lno = _tb.tb_lineno
                log.error("filter_urls: [%s] ignore %s from callback %s:%s", _name, repr(exc), _fn, _lno)
                continue

            if isinstance(_url, str):
                log.debug("filter_urls: [%s] URL %s -> %s", _name, _ref.url, _url)
                _ref.url = _url
            elif not _url:
                log.debug("filter_urls: [%s] drop ref %s", _name, _ref)
                self.formats.remove(_ref)

        return super().filter_urls(filter_func)
