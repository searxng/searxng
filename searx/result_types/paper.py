# SPDX-License-Identifier: AGPL-3.0-or-later
"""Typification of the *paper* results.

.. _BibTeX field types: https://en.wikipedia.org/wiki/BibTeX#Field_types
.. _BibTeX format: https://www.bibtex.com/g/bibtex-format/

Results of this type are rendered in the :origin:`paper.html
<searx/templates/simple/result_templates/paper.html>` template.

Related topics:

- `BibTeX field types`_
- `BibTeX format`_

----

.. autoclass:: Paper
   :members:
   :show-inheritance:

"""
# pylint: disable=too-few-public-methods, disable=invalid-name

# Struct fields aren't discovered in Python 3.14
# - https://github.com/searxng/searxng/issues/5284
from __future__ import annotations

__all__ = ["Paper"]

import typing as t

from searx.weather import DateTime
from ._base import MainResult


@t.final
class Paper(MainResult, kw_only=True):
    """Result type suitable for displaying scientific papers and other
    documents."""

    template: str = "paper.html"

    date_of_publication: DateTime | None = None
    """Date the document was published."""

    content: str = ""
    """An abstract or excerpt from the document."""

    comments: str = ""
    """Free text display in italic below the content."""

    tags: list[str] = []
    """Free tag list."""

    type: str = ""
    """Short description of medium type, e.g. *book*, *pdf* or *html* ..."""

    authors: list[str] | set[str] = []
    """List of authors of the work (authors with a "s" suffix, the "author" is
    in the :py:obj:`MainResult.author`)."""

    editor: str = ""
    """Editor of the book/paper."""

    publisher: str = ""
    """Name of the publisher."""

    journal: str = ""
    """Name of the journal or magazine the article was published in."""

    volume: str | int = ""
    """Volume number."""

    pages: str = ""
    """Page range where the article is."""

    number: str = ""
    """Number of the report or the issue number for a journal article."""

    doi: str = ""
    """DOI number (like ``10.1038/d41586-018-07848-2``)."""

    issn: list[str] = []
    """List of ISSN numbers like ``1476-4687``"""

    isbn: list[str] = []
    """List of ISBN numbers like ``9780201896831``"""

    pdf_url: str = ""
    """URL to the full article, the PDF version"""

    html_url: str = ""
    """URL to full article, HTML version"""

    def __post_init__(self):
        super().__post_init__()
        if self.date_of_publication is None and self.publishedDate is not None:
            self.date_of_publication = DateTime(self.publishedDate)
