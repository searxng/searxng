# SPDX-License-Identifier: AGPL-3.0-or-later
"""Implementation of the :py:obj:`preference <searx.preference>` settings."""
# pylint: disable = too-few-public-methods

import typing as t
import msgspec


class SettingsPref(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    """Options for configuring the preferences

    .. code:: yaml

       preferences:
         lock:
           - favicon_resolver
           - image_proxy
           - method
       # ...

    """

    lock: set[
        t.Literal[
            "categories",
            "language",
            "locale",
            "autocomplete",
            "favicon_resolver",
            "image_proxy",
            "method",
            "safesearch",
            "theme",
            "results_on_new_tab",
            "doi_resolver",
            "simple_style",
            "center_alignment",
            "query_in_title",
            "search_on_category_select",
        ]
    ] = set()
    """Lock arbitrary settings on the preferences page."""
