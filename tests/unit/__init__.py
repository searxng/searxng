import os
from os.path import dirname, sep, abspath

# In unit tests the user settings from unit/settings/test_settings.yml are used.
os.environ['SEARXNG_SETTINGS_PATH'] = abspath(dirname(__file__) + sep + 'settings' + sep + 'test_settings.yml')
