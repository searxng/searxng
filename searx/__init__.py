'''
searx is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

searx is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with searx. If not, see < http://www.gnu.org/licenses/ >.

(C) 2013- by Adam Tauber, <asciimoo@gmail.com>
'''

import logging
import searx.settings_loader
from searx.settings_defaults import settings_set_defaults
from os.path import dirname, abspath


searx_dir = abspath(dirname(__file__))
searx_parent_dir = abspath(dirname(dirname(__file__)))
settings, settings_load_message = searx.settings_loader.load_settings()

if settings is not None:
    settings = settings_set_defaults(settings)

searx_debug = settings['general']['debug']
if searx_debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger('searx')
logger.info(settings_load_message)

# log max_request_timeout
max_request_timeout = settings['outgoing']['max_request_timeout']
if max_request_timeout is None:
    logger.info('max_request_timeout=%s', repr(max_request_timeout))
else:
    logger.info('max_request_timeout=%i second(s)', max_request_timeout)


class _brand_namespace:

    @classmethod
    def get_val(cls, group, name, default=''):
        return settings.get(group, {}).get(name) or default

    @property
    def SEARX_URL(self):
        return self.get_val('server', 'base_url')

    @property
    def CONTACT_URL(self):
        return self.get_val('general', 'contact_url')

    @property
    def GIT_URL(self):
        return self.get_val('brand', 'git_url')

    @property
    def GIT_BRANCH(self):
        return self.get_val('brand', 'git_branch')

    @property
    def ISSUE_URL(self):
        return self.get_val('brand', 'issue_url')

    @property
    def NEW_ISSUE_URL(self):
        return self.get_val('brand', 'new_issue_url')

    @property
    def DOCS_URL(self):
        return self.get_val('brand', 'docs_url')

    @property
    def PUBLIC_INSTANCES(self):
        return self.get_val('brand', 'public_instances')

    @property
    def WIKI_URL(self):
        return self.get_val('brand', 'wiki_url')

    @property
    def TWITTER_URL(self):
        return self.get_val('brand', 'twitter_url')


brand = _brand_namespace()
