# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import searx.limiter
from searx import settings

from tests import SearxTestCase


class LimiterInitializeTest(SearxTestCase):

    def setUp(self):
        super().setUp()
        self.addCleanup(self._reset_limiter_cfg)

    def _reset_limiter_cfg(self):
        searx.limiter.CFG = None
        searx.limiter._INSTALLED = False

    def _settings_with(self, *, limiter_enabled: bool, public_instance: bool = False):
        test_settings = deepcopy(settings)
        test_settings['server']['limiter'] = limiter_enabled
        test_settings['server']['public_instance'] = public_instance
        return test_settings

    def test_initialize_skips_missing_limiter_warning_when_disabled(self):
        with TemporaryDirectory() as tempdir:
            with patch('searx.settings_loader.get_user_cfg_folder', return_value=Path(tempdir)):
                with patch('searx.limiter.valkeydb.client', return_value=None):
                    with patch('searx.limiter.botdetection.init') as botdetection_init:
                        with self.assertNoLogs('searx.botdetection.config', level='WARNING'):
                            searx.limiter.initialize(self.app, self._settings_with(limiter_enabled=False))

        botdetection_init.assert_called_once()

    def test_initialize_warns_about_missing_limiter_config_when_enabled(self):
        with TemporaryDirectory() as tempdir:
            with patch('searx.settings_loader.get_user_cfg_folder', return_value=Path(tempdir)):
                with patch('searx.limiter.valkeydb.client', return_value=None):
                    with patch('searx.limiter.botdetection.init'):
                        with self.assertLogs('searx.botdetection.config', level='WARNING') as logs:
                            searx.limiter.initialize(self.app, self._settings_with(limiter_enabled=True))

        self.assertIn('missing config file', logs.output[0])
