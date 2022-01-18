from flask_babel import gettext
from . import Resource

name = gettext('Infinite scroll')
description = gettext('Automatically load next page when scrolling to bottom of current page')
default_on = False
preference_section = 'ui'

js_dependencies = (Resource(path='plugins/js/infinite_scroll.js', themes=('oscar',)),)
css_dependencies = (Resource(path='plugins/css/infinite_scroll.css', themes=('oscar',)),)
