#!/usr/bin/env python
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


class LogicodevStyle(Style):  # pylint: disable=R0903
    """Logicodev style
    based on https://github.com/searx/searx/blob/2a5c39e33c3306ca17e09211fbf5a0f785cb10c8/searx/static/themes/oscar/less/logicodev/code.less
    """  # pylint: disable=C0301

    background_color = '#282C34'

    styles = {
        Comment:                "#556366 italic",
        Comment.Multiline:      "#556366 italic",
        Comment.Preproc:        "#BC7A00",
        Comment.Single:         "#556366 italic",
        Comment.Special:        "#556366 italic",
        Error:                  "border:#ff0000",
        Generic.Deleted:        "#A00000",
        Generic.Emph:           "italic",
        Generic.Error:          "#FF0000",
        Generic.Heading:        "#000080 bold",
        Generic.Inserted:       "#00A000",
        Generic.Output:         "#888888",
        Generic.Prompt:         "#000080 bold",
        Generic.Strong:         "bold",
        Generic.Subheading:     "#800080 bold",
        Generic.Traceback:      "#0044DD",
        Keyword:                "#BE74D5 bold",
        Keyword.Constant:       "#BE74D5 bold",
        Keyword.Declaration:    "#BE74D5 bold",
        Keyword.Namespace:      "#BE74D5 bold",
        Keyword.Pseudo:         "#BE74D5",
        Keyword.Reserved:       "#BE74D5 bold",
        Keyword.Type:           "#D46C72",
        Literal.Number:         "#D19A66",
        Literal.String:         "#86C372",
        Literal.String.Backtick:"#86C372",
        Literal.String.Char:    "#86C372",
        Literal.String.Doc:     "#86C372 italic",
        Literal.String.Double:  "#86C372",
        Literal.String.Escape:  "#BB6622 bold",
        Literal.String.Heredoc: "#86C372",
        Literal.String.Interpol:"#BB6688 bold",
        Literal.String.Other:   "#BE74D5",
        Literal.String.Regex:   "#BB6688",
        Literal.String.Single:  "#86C372",
        Literal.String.Symbol:  "#DFC06F",
        Name.Attribute:         "#7D9029",
        Name.Builtin:           "#BE74D5",
        Name.Builtin.Pseudo:    "#BE74D5",
        Name.Class:             "#61AFEF bold",
        Name.Constant:          "#D19A66",
        Name.Decorator:         "#AA22FF",
        Name.Entity:            "#999999 bold",
        Name.Exception:         "#D2413A bold",
        Name.Function:          "#61AFEF",
        Name.Label:             "#A0A000",
        Name.Namespace:         "#61AFEF bold",
        Name.Tag:               "#BE74D5 bold",
        Name.Variable:          "#DFC06F",
        Name.Variable.Class:    "#DFC06F",
        Name.Variable.Global:   "#DFC06F",
        Name.Variable.Instance: "#DFC06F",
        Operator:               "#D19A66",
        Operator.Word:          "#AA22FF bold",
        Text.Whitespace:        "#D7DAE0",
    }


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
        if ' ' in line  and not line.startswith(cssclass):
            line = cssclass + ' ' + line
        result += line + '\n'
    return result


def main():

    fname = 'static/themes/oscar/src/generated/pygments-logicodev.less'
    print("update: %s" % fname)
    with open(get_output_filename(fname), 'w') as f:
        f.write(get_css(CSSCLASS, LogicodevStyle))

    fname = 'static/themes/oscar/src/generated/pygments-pointhi.less'
    print("update: %s" % fname)
    with open(get_output_filename(fname), 'w') as f:
        f.write(get_css(CSSCLASS, 'default'))

    fname = 'static/themes/simple/src/generated/pygments.less'
    print("update: %s" % fname)
    with open(get_output_filename(fname), 'w') as f:
        f.write(get_css(CSSCLASS, 'default'))


if __name__ == '__main__':
    main()
