# SPDX-License-Identifier: AGPL-3.0-or-later
"""Typification of the *video* results.  Results of this type are rendered in
the :origin:`videos.html <searx/templates/simple/result_templates/videos.html>`
template.

.. autoclass:: Video
   :members:
   :show-inheritance:
"""

# pylint: disable=too-few-public-methods
__all__ = ["Video"]

import typing as t

from searx.utils import get_embedded_stream_url
from ._base import MainResult


@t.final
class Video(MainResult, kw_only=True):
    """Result type suitable for displaying videos."""

    template: str = "videos.html"

    def __post_init__(self):
        super().__post_init__()

        if self.url and not self.iframe_src:
            self.iframe_src = get_embedded_stream_url(self.url)
