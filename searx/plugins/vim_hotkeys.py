from flask_babel import gettext
from . import Resource

name = gettext('Vim-like hotkeys')
description = gettext(
    'Navigate search results with Vim-like hotkeys '
    '(JavaScript required). '
    'Press "h" key on main or result page to get help.'
)
default_on = False
preference_section = 'ui'

js_dependencies = (
    Resource(path='plugins/js/vim_hotkeys.js', themes=('oscar',)),
    Resource(path='themes/simple/src/js/plugins/vim_hotkeys.js', themes=('simple',)),
)
css_dependencies = (Resource(path='plugins/css/vim_hotkeys.css', themes=('oscar',)),)
