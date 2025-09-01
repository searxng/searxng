#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Update pygments style

Call this script after each upgrade of pygments

"""
# pylint: disable=too-few-public-methods

from pathlib import Path
import pygments
from pygments.formatters.html import HtmlFormatter

from searx import searx_dir

LESS_FILE = Path(searx_dir).parent / 'client/simple/generated/pygments.less'

HEADER = f"""\
// SPDX-License-Identifier: AGPL-3.0-or-later

/*
   this file is generated automatically by searxng_extra/update/update_pygments.py
   using pygments version {pygments.__version__}:

       ./manage templates.simple.pygments
*/

"""

START_LIGHT_THEME = """
.code-highlight {
"""

END_LIGHT_THEME = """
}
"""

START_DARK_THEME = """
.code-highlight-dark(){
  .code-highlight {
"""

END_DARK_THEME = """
  }
}
"""


class Formatter(HtmlFormatter):  # pylint: disable=missing-class-docstring

    def get_style_lines(self, arg=None):
        style_lines = []
        style_lines.extend(self.get_linenos_style_defs())
        style_lines.extend(self.get_background_style_defs(arg))
        style_lines.extend(self.get_token_style_defs(arg))
        return style_lines


def generat_css(light_style, dark_style) -> str:
    css = HEADER + START_LIGHT_THEME
    for line in Formatter(style=light_style).get_style_lines():
        css += '\n  ' + line
    css += END_LIGHT_THEME + START_DARK_THEME
    for line in Formatter(style=dark_style).get_style_lines():
        css += '\n    ' + line
    css += END_DARK_THEME
    return css


if __name__ == '__main__':
    print("update: %s" % LESS_FILE)
    with LESS_FILE.open('w', encoding='utf8') as f:
        f.write(generat_css('default', 'monokai'))
