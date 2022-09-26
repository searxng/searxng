# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Services managed by SearXNG"""

from pathlib import Path
import tempfile

# hapless files are stored in /tmp/SearXNG .. may be we should store them on a
# different location.
SEARXNG_HAP_DIR = Path(tempfile.gettempdir()) / "SearXNG"
