# SPDX-License-Identifier: AGPL-3.0-or-later
"""Typification of the *image* results.  Results of this type are rendered in
the :origin:`images.html <searx/templates/simple/result_templates/images.html>`
template.

.. autoclass:: Image
   :members:
   :show-inheritance:

"""

__all__ = ["Image"]

import typing as t


from ._base import MainResult


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
    """The format of the image (e.g. ``png``)."""

    source: str = ""
    """Source of the image."""

    filesize: str = ""
    """Size of bytes in :py:obj:`human readable <searx.humanize_bytes>` notation
    (e.g. ``1MB`` for ``1024*1024`` Bytes filesize)."""
