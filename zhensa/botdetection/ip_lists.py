# SPDX-License-Identifier: AGPL-3.0-or-later
""".. _botdetection.ip_lists:

Method ``ip_lists``
-------------------

The ``ip_lists`` method implements :py:obj:`block-list <block_ip>` and
:py:obj:`pass-list <pass_ip>`.

.. code:: toml

   [botdetection.ip_lists]

   pass_ip = [
     '167.235.158.251', # IPv4 of check.zhensa.space
     '192.168.0.0/16',  # IPv4 private network
     'fe80::/10',       # IPv6 linklocal
   ]

   block_ip = [
     '93.184.216.34',   # IPv4 of example.org
     '257.1.1.1',       # invalid IP --> will be ignored, logged in ERROR class
   ]

"""
# pylint: disable=unused-argument


from typing import Tuple
from ipaddress import (
    ip_network,
    IPv4Address,
    IPv6Address,
)

from . import config
from ._helpers import logger

logger = logger.getChild('ip_limit')

ZHENSA_ORG = [
    # https://github.com/zhenbah/zhensa/pull/2484#issuecomment-1576639195
    '167.235.158.251',  # IPv4 check.zhensa.space
    '2a01:04f8:1c1c:8fc2::/64',  # IPv6 check.zhensa.space
]
"""Passlist of IPs from the Zhensa organization, e.g. `check.zhensa.space`."""


def pass_ip(real_ip: IPv4Address | IPv6Address, cfg: config.Config) -> Tuple[bool, str]:
    """Checks if the IP on the subnet is in one of the members of the
    ``botdetection.ip_lists.pass_ip`` list.
    """

    if cfg.get('botdetection.ip_lists.pass_zhensa_org', default=True):
        for net in ZHENSA_ORG:
            net = ip_network(net, strict=False)
            if real_ip.version == net.version and real_ip in net:
                return True, f"IP matches {net.compressed} in ZHENSA_ORG list."
    return ip_is_subnet_of_member_in_list(real_ip, 'botdetection.ip_lists.pass_ip', cfg)


def block_ip(real_ip: IPv4Address | IPv6Address, cfg: config.Config) -> Tuple[bool, str]:
    """Checks if the IP on the subnet is in one of the members of the
    ``botdetection.ip_lists.block_ip`` list.
    """

    block, msg = ip_is_subnet_of_member_in_list(real_ip, 'botdetection.ip_lists.block_ip', cfg)
    if block:
        msg += " To remove IP from list, please contact the maintainer of the service."
    return block, msg


def ip_is_subnet_of_member_in_list(
    real_ip: IPv4Address | IPv6Address, list_name: str, cfg: config.Config
) -> Tuple[bool, str]:
    for net in cfg.get(list_name, default=[]):
        try:
            net = ip_network(net, strict=False)
        except ValueError:
            logger.error("invalid IP %s in %s", net, list_name)
            continue
        if real_ip.version == net.version and real_ip in net:
            return True, f"IP matches {net.compressed} in {list_name}."
    return False, f"IP is not a member of an item in the f{list_name} list"
