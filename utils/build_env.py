# SPDX-License-Identifier: AGPL-3.0-or-later
"""build environment used by shell scripts
"""

# set path
import sys
import os
from os.path import realpath, dirname, join, sep, abspath

repo_root = realpath(dirname(realpath(__file__)) + sep + '..')
sys.path.insert(0, repo_root)

# Assure that the settings file from reposetorie's working tree is used to
# generate the build_env, not from /etc/searxng/settings.yml.
os.environ['SEARXNG_SETTINGS_PATH'] = join(repo_root, 'etc', 'settings.yml')

def _env(*arg, **kwargs):
    val = get_setting(*arg, **kwargs)
    if val is True:
        val = '1'
    elif val is False:
        val = ''
    return val

# If you add or remove variables here, do not forget to update:
# - ./docs/admin/engines/settings.rst
# - ./docs/dev/makefile.rst (section make buildenv)

name_val = [

    ('SEARXNG_URL'              , 'server.base_url'),
    ('SEARXNG_PORT'             , 'server.port'),
    ('SEARXNG_BIND_ADDRESS'     , 'server.bind_address'),

]

brand_env = 'utils' + sep + 'brand.env'

# Some defaults in the settings.yml are taken from the environment,
# e.g. SEARXNG_BIND_ADDRESS (:py:obj:`searx.settings_defaults.SHEMA`).  When the
# 'brand.env' file is created these envirnoment variables should be unset first::

_unset = object()
for name, option in name_val:
    if not os.environ.get(name, _unset) is _unset:
        del os.environ[name]

# After the variables are unset in the environ, we can import from the searx
# package (what will read the values from the settings.yml).

from searx.version import GIT_URL, GIT_BRANCH
from searx import get_setting

print('build %s (settings from: %s)' % (brand_env, os.environ['SEARXNG_SETTINGS_PATH']))
sys.path.insert(0, repo_root)

with open(repo_root + sep + brand_env, 'w', encoding='utf-8') as f:
    for name, option in name_val:
        print("export %s='%s'" % (name, _env(option)), file=f)
    print(f"export GIT_URL='{GIT_URL}'", file=f)
    print(f"export GIT_BRANCH='{GIT_BRANCH}'", file=f)
