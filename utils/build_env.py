# SPDX-License-Identifier: AGPL-3.0-or-later
"""build environment used by shell scripts
"""

# set path
import sys
import os
from os.path import realpath, dirname, join, sep, abspath

repo_root = realpath(dirname(realpath(__file__)) + sep + '..')
sys.path.insert(0, repo_root)

# Under the assumption that a brand is always a fork assure that the settings
# file from reposetorie's working tree is used to generate the build_env, not
# from /etc/searx/settings.yml.
os.environ['SEARX_SETTINGS_PATH'] = abspath(dirname(__file__) + sep + 'settings.yml')

def _env(*arg, **kwargs):
    val = get_setting(*arg, **kwargs)
    if val is True:
        val = '1'
    elif val is False:
        val = ''
    return val

name_val = [
    ('SEARX_URL'              , 'server.base_url'),
    ('GIT_URL'                , 'brand.git_url'),
    ('GIT_BRANCH'             , 'brand.git_branch'),
    ('ISSUE_URL'              , 'brand.issue_url'),
    ('DOCS_URL'               , 'brand.docs_url'),
    ('PUBLIC_INSTANCES'       , 'brand.public_instances'),
    ('WIKI_URL'               , 'brand.wiki_url'),
]

brand_env = 'utils' + sep + 'brand.env'

# Some defaults in the settings.yml are taken from the environment,
# e.g. SEARX_BIND_ADDRESS (:py:obj:`searx.settings_defaults.SHEMA`).  When the
# 'brand.env' file is created these enviroment variables should be unset first::

_unset = object()
for name, option in name_val:
    if not os.environ.get(name, _unset) is _unset:
        del os.environ[name]

# After the variables are unset in the environ, we can import settings
# (get_setting) from searx module.

from searx import get_setting

print('build %s (settings from: %s)' % (brand_env, os.environ['SEARX_SETTINGS_PATH']))
sys.path.insert(0, repo_root)
from searx import settings

with open(repo_root + sep + brand_env, 'w', encoding='utf-8') as f:
    for name, option in name_val:
        print("export %s='%s'" % (name, _env(option)), file=f)
