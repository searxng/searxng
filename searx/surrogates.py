# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""
Allow to replace some objects using settings.yml to lower fork maintenance.
"""

import sys
from importlib import import_module
from functools import wraps

from searx import settings, logger

logger = logger.getChild('surrogates')


def _get_obj_by_name(name):
    module_name, obj_name = name.rsplit('.', 1)
    if module_name not in sys.modules:
        module = import_module(module_name)
    else:
        module = sys.modules[module_name]
    return getattr(module, obj_name, None)


def get_actual_object(name, obj):
    surrogate_name = settings['surrogates'].get(name)
    actual_obj = _get_obj_by_name(surrogate_name) if surrogate_name else obj
    logger.info('Replace "%s" with "%s"', name, surrogate_name)
    if not callable(actual_obj):
        raise ValueError(f"{surrogate_name} is not callable")

    @wraps(obj)
    def wrapped(*args, **kwargs):
        return actual_obj(*args, **kwargs)
    return wrapped
