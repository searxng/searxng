# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

import os
from pathlib import Path

# By default, in unit tests the user settings from
# unit/settings/test_settings.yml are used.

os.environ['SEARXNG_SETTINGS_PATH'] = str(Path(__file__).parent / "settings" / "test_settings.yml")
