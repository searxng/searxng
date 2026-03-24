# SPDX-License-Identifier: AGPL-3.0-or-later
"""Implementations needed for a branding of SearXNG."""
# pylint: disable=too-few-public-methods

# Struct fields aren't discovered in Python 3.14
# - https://github.com/searxng/searxng/issues/5284
from __future__ import annotations

__all__ = ["SettingsBrand"]

import msgspec


class BrandCustom(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    """Custom settings in the brand section."""

    links: dict[str, str] = {}
    """Custom entries in the footer of the WEB page: ``[title]: [link]``"""


class SettingsBrand(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    """Options for configuring brand properties.

    .. code:: yaml

       brand:
         issue_url: https://github.com/searxng/searxng/issues
         docs_url: https://docs.searxng.org
         public_instances: https://searx.space
         wiki_url: https://github.com/searxng/searxng/wiki

         custom:
           links:
             Uptime: https://uptime.searxng.org/history/example-org
             About: https://example.org/user/about.html
    """

    issue_url: str = "https://github.com/searxng/searxng/issues"
    """If you host your own issue tracker change this URL."""

    docs_url: str = "https://docs.searxng.org"
    """If you host your own documentation change this URL."""

    public_instances: str = "https://searx.space"
    """If you host your own https://searx.space change this URL."""

    wiki_url: str = "https://github.com/searxng/searxng/wiki"
    """Link to your wiki (or ``false``)"""

    custom: BrandCustom = msgspec.field(default_factory=BrandCustom)
    """Optional customizing.

    .. autoclass:: searx.brand.BrandCustom
       :members:
    """
