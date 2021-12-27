# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""
if setproctitle is installed.
set Unix thread name with the Python thread name
"""

try:
    import setproctitle
except ImportError:
    pass
else:
    import threading

    old_thread_init = threading.Thread.__init__

    def new_thread_init(self, *args, **kwargs):
        # pylint: disable=protected-access, disable=c-extension-no-member
        old_thread_init(self, *args, **kwargs)
        setproctitle.setthreadtitle(self._name)

    threading.Thread.__init__ = new_thread_init
