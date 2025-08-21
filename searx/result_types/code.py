# SPDX-License-Identifier: AGPL-3.0-or-later
"""Typification of the *code* results.  Results of this type are rendered in
the :origin:`code.html <searx/templates/simple/result_templates/code.html>`
template.  For highlighting the code passages, Pygments is used.

.. _Pygments:  https://pygments.org

----

.. autoclass:: Code
   :members:
   :show-inheritance:

"""
# pylint: disable=too-few-public-methods, disable=invalid-name

from __future__ import annotations

__all__ = ["Code"]

import typing as t

from pygments import highlight  # pyright: ignore[reportUnknownVariableType]
from pygments.lexers._mapping import LEXERS  # pyright: ignore[reportMissingTypeStubs]
from pygments.lexers import guess_lexer, get_lexer_by_name, guess_lexer_for_filename
from pygments.util import ClassNotFound
from pygments.formatters import HtmlFormatter  # pylint: disable=no-name-in-module

from ._base import MainResult


_pygments_languages: list[str] = []


def is_valid_language(code_language: str) -> bool:
    """Checks if the specified ``code_language`` is known in Pygments."""
    if not _pygments_languages:
        for l in LEXERS.values():
            # l[2] is the tuple with the alias names
            for alias_name in l[2]:
                _pygments_languages.append(alias_name.lower())
    return code_language.lower() in _pygments_languages


@t.final
class Code(MainResult, kw_only=True):
    """Simple table view which maps *key* names (first col) to *values*
    (second col)."""

    template: str = "code.html"

    repository: str | None = None
    """A link related to a repository related to the *result*"""

    codelines: list[tuple[int, str]] = []
    """A list of two digit tuples where the first item is the line number and
    the second item is the code line."""

    hl_lines: set[int] = set()
    """A list of line numbers to highlight"""

    code_language: str = "<guess>"
    """Pygment's short name of the lexer, e.g. ``text`` for the
    :py:obj:`pygments.lexers.special.TextLexer`.  For a list of available
    languages consult: `Pygments languages`_.  If the language is not in this
    list, a :py:obj:`ValueError` is raised.

    The default is ``<guess>`` which has a special meaning;

    - If :py:obj:`Code.filename` is set, Pygment's factory method
      :py:obj:`pygments.lexers.guess_lexer_for_filename` is used to determine
      the language of the ``codelines``.

    - else Pygment's :py:obj:`pygments.lexers.guess_lexer` factory is used.

    In case the language can't be detected, the fallback is ``text``.

    .. _Pygments languages:  https://pygments.org/languages/
    """

    filename: str | None = None
    """Optional file name, can help to ``<guess>`` the language of the code (in
    case of ambiguous short code examples).  If :py:obj:`Code.title` is not set,
    its default is the filename."""

    strip_new_lines: bool = True
    """Strip leading and trailing newlines for each returned fragment.
    Single file might return multiple code fragments.
    """

    strip_whitespace: bool = False
    """Strip all leading and trailing whitespace for each returned fragment.
    Single file might return multiple code fragments. Enabling this might break
    code indentation.
    """

    def __post_init__(self):
        super().__post_init__()

        if not self.title and self.filename:
            self.title = self.filename

        if self.code_language != "<guess>" and not is_valid_language(self.code_language):
            raise ValueError(f"unknown code_language: {self.code_language}")

    def __hash__(self):
        """The hash value is build up from URL and code lines. :py:obj:`Code
        <Result.__eq__>` objects are equal, when the hash values of both objects
        are equal.
        """
        return hash(f"{self.url} {self.codelines}")

    def get_lexer(self):
        if self.code_language != "<guess>":
            return get_lexer_by_name(self.code_language)

        src_code = "\n".join([l[1] for l in self.codelines])
        if self.filename:
            try:
                return guess_lexer_for_filename(self.filename, src_code)
            except ClassNotFound:
                pass
        try:
            return guess_lexer(src_code)
        except ClassNotFound:
            pass
        return get_lexer_by_name("text")

    def HTML(self, **options) -> str:  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
        """Rendered HTML, additional options are accepted, for more details have
        a look at HtmlFormatter_.

        .. _HtmlFormatter: https://pygments.org/docs/formatters/#HtmlFormatter
        """
        lexer = self.get_lexer()

        line_no: int = 0  # current line number
        code_block_start: int = 0  # line where the current code block starts
        code_block_end: int | None = None  # line where the current code ends
        code_block: list[str] = []  # lines of the current code block
        html_code_blocks: list[str] = []  # HTML representation of all code blocks

        def _render(**kwargs):  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
            for k, default in [
                ("linenos", "inline"),
                ("linenostart", code_block_start),
                ("cssclass", "code-highlight"),
                ("hl_lines", [hl - code_block_start + 1 for hl in self.hl_lines]),
            ]:
                kwargs[k] = kwargs.get(k, default)  # pyright: ignore[reportUnknownMemberType]

            # Wrap the code inside <pre> blocks using <code>, as recommended by
            # the HTML5 specification (default is False).  Do we need this?
            kwargs["wrapcode"] = kwargs.get("wrapcode", True)

            html_code_blocks.append(
                highlight(
                    "\n".join(code_block),
                    lexer,
                    HtmlFormatter(**kwargs),  # pyright: ignore[reportUnknownArgumentType]
                )
            )

        for line_no, code_line in self.codelines:
            if code_block_end is None:
                # initial start condition
                code_block_start = line_no

            if code_block_end is not None and code_block_end + 1 != line_no:
                # new code block is detected, render current code block
                _render(**options)  # pyright: ignore[reportUnknownArgumentType]
                # reset conditions for next code block, which first line is the
                # current code line
                code_block = [code_line]
                code_block_start = line_no
                code_block_end = line_no
                continue

            # add line to the current code block and update last line n
            code_block.append(code_line)
            code_block_end = line_no

        # highlight (last) code block
        _render(**options)  # pyright: ignore[reportUnknownArgumentType]
        return "\n".join(html_code_blocks)
