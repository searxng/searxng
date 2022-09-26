# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""A hapless command line wrapper suitable for SearXNG.

In a development environment try::

    $ ./manage pyenv.cmd bash
    (py3) $ python -m searx.services --help
"""

import os
import asyncio
import time

from pathlib import Path

try:
    from shlex import join as shlex_join
except ImportError:
    # Fallback for Python 3.7
    from hapless.utils import shlex_join_backport as shlex_join

from string import Template
from typing import Optional

from hapless import cli
from hapless.main import Hapless

from searx.settings_loader import load_yaml
from . import SEARXNG_HAP_DIR

SEARXNG_SERVICES_CONFIG = Path(__file__).parent / 'config.yml'
CONFIG_ENV = {
    'SEARXNG_ROOT': SEARXNG_SERVICES_CONFIG.parent.parent.parent,
    'HOME': os.environ['HOME'],
}


class SearXNGHapless(Hapless):
    """Adjustments to :py:class:`Hapless` class

    ToDo fix upstrem: the methods should never call sys.exit
    """

    def run(self, cmd: str, name: Optional[str] = None, check: bool = False):
        hap = self.create_hap(cmd=cmd, name=name)
        pid = os.fork()
        if pid == 0:
            coro = self.run_hap(hap)
            asyncio.run(coro)
        else:
            if check:
                self._check_fast_failure(hap)
            # sys.exit(0)


def _parse_cmd(service_cfg):
    cmd = []
    for item in service_cfg.get('cmd', []):
        cmd.append(Template(item).substitute(**CONFIG_ENV))
    return shlex_join(cmd)


@cli.cli.command(short_help="Start SearXNG services from YAML config (ToDo)")
@cli.click.argument("config", metavar="config", default=SEARXNG_SERVICES_CONFIG)
def sxng_start(config):
    # print("START services from YAML config file --> %s" % config)
    cfg = load_yaml(config).get('services', {})
    cli.hapless.clean()
    for name, service_cfg in cfg.items():
        hap = cli.hapless.get_hap(name)
        if hap is not None:
            cli.console.print(
                f"{cli.config.ICON_INFO} Hap with such name already exists: {hap}",
                style=f"{cli.config.COLOR_ERROR} bold",
            )
            continue
        cmd = _parse_cmd(service_cfg)
        cli.hapless.run(cmd, name=name)


@cli.cli.command(short_help="TODO: Stop SearXNG services from YAML config (ToDo)")
@cli.click.argument("config", metavar="config", default=SEARXNG_SERVICES_CONFIG)
def sxng_stop(config):
    # print("STOP services from YAML config file --> %s" % config)
    cfg = load_yaml(config).get('services', {})
    hap_list = []
    for name, _ in cfg.items():
        hap = cli.hapless.get_hap(name)
        if hap is not None:
            hap_list.append(hap)
    if hap_list:
        cli.hapless.kill(hap_list)
        # wait a second to close open handles
        time.sleep(1)
        cli.hapless.clean()


#    import pdb
#    pdb.set_trace()

if __name__ == "__main__":
    cli.hapless = SearXNGHapless(hapless_dir=SEARXNG_HAP_DIR)
    cli.cli()  # pylint: disable=no-value-for-parameter
