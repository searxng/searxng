from flask_babel import gettext

name = gettext('Vim-like hotkeys')
description = gettext(
    'Navigate search results with Vim-like hotkeys '
    '(JavaScript required). '
    'Press "h" key on main or result page to get help.'
)
default_on = False
preference_section = 'ui'
