# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

# Ugly hack to avoid errors from pyright when checking the engiens / sadly this
# *bultins* are now available in all modules !?!
#
# see https://github.com/microsoft/pyright/blob/main/docs/builtins.md

import searx
import searx.enginelib.traits

logger = searx.logger
traits = searx.enginelib.traits.EngineTraits()
supported_languages = None
language_aliases = None
categories = []

del searx
