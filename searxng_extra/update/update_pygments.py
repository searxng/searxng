#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Update pygments style

Call this script after each upgrade of pygments
"""

# pylint: disable=C0116

# set path
from os.path import join
import pygments
from pygments.formatters import HtmlFormatter  # pylint: disable=E0611
from pygments.style import Style
from pygments.token import Comment, Error, Generic, Keyword, Literal, Name, Operator, Text

from searx import searx_dir

CSSCLASS = '.code-highlight'
RULE_CODE_LINENOS = """ .linenos {
    -webkit-touch-callout: none;
    -webkit-user-select: none;
    -khtml-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
    user-select: none;
    cursor: default;

    &::selection {
        background: transparent; /* WebKit/Blink Browsers */
    }
    &::-moz-selection {
        background: transparent; /* Gecko Browsers */
    }

    margin-right: 8px;
    text-align: right;
}"""


def get_output_filename(relative_name):
    return join(searx_dir, relative_name)


def get_css(cssclass, style):
    result = f"""/*
   this file is generated automatically by searxng_extra/update/update_pygments.py
   using pygments version {pygments.__version__}
*/\n\n"""
    css_text = HtmlFormatter(style=style).get_style_defs(cssclass)
    result += cssclass + RULE_CODE_LINENOS + '\n\n'
    for line in css_text.splitlines():
        if ' ' in line and not line.startswith(cssclass):
            line = cssclass + ' ' + line
        result += line + '\n'
    return result


def main():

    fname = 'static/themes/simple/src/generated/pygments.less'
    print("update: %s" % fname)
    with open(get_output_filename(fname), 'w') as f:
        f.write(get_css(CSSCLASS, 'default'))


if __name__ == '__main__':
    main()
