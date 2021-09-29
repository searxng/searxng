from flask_babel import gettext

name = gettext('Vim-like hotkeys')
description = gettext('Navigate search results with Vim-like hotkeys '
                      '(JavaScript required). '
                      'Press "h" key on main or result page to get help.')
default_on = False
preference_section = 'ui'

js_dependencies = ('plugins/js/vim_hotkeys.js',)
css_dependencies = ('plugins/css/vim_hotkeys.css',)
