# SPDX-License-Identifier: AGPL-3.0-or-later
"""build environment used by shell scripts
"""

# set path
import sys
import os
from os.path import realpath, dirname, join, sep, abspath

repo_root = realpath(dirname(realpath(__file__)) + sep + '..')
sys.path.insert(0, repo_root)
os.environ['SEARX_SETTINGS_PATH'] = abspath(dirname(__file__) + '/settings.yml')

# Under the assumption that a brand is always a fork assure that the settings
# file from reposetorie's working tree is used to generate the build_env, not
# from /etc/searx/settings.yml.
os.environ['SEARX_SETTINGS_PATH'] = abspath(dirname(__file__) + sep + 'settings.yml')

from searx import get_setting

def _env(*arg, **kwargs):
    val = get_setting(*arg, **kwargs)
    if val is True:
        val = '1'
    elif val is False:
        val = ''
    return val

name_val = [
    ('SEARX_URL'              , _env('server.base_url','')),
    ('GIT_URL'                , _env('brand.git_url', '')),
    ('GIT_BRANCH'             , _env('brand.git_branch', '')),
    ('ISSUE_URL'              , _env('brand.issue_url', '')),
    ('DOCS_URL'               , _env('brand.docs_url', '')),
    ('PUBLIC_INSTANCES'       , _env('brand.public_instances', '')),
    ('CONTACT_URL'            , _env('general.contact_url', '')),
    ('WIKI_URL'               , _env('brand.wiki_url', '')),
    ('TWITTER_URL'            , _env('brand.twitter_url', '')),
]

brand_env = 'utils' + sep + 'brand.env'

print('build %s' % brand_env)
with open(repo_root + sep + brand_env, 'w', encoding='utf-8') as f:
    for name, val in name_val:
        print("export %s='%s'" % (name, val), file=f)
