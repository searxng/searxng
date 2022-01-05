# -*- coding: utf-8; mode: sh -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# shellcheck shell=bash disable=SC2034
#
# This file should be edited only ones just before the installation of any
# service is done.  After the installation of the searx service a copy of this
# file is placed into the $SEARX_SRC of the instance, e.g.::
#
#     /usr/local/searx/searx-src/.config.sh
#
# .. hint::
#
#    Before you change a value here, You have to fully uninstall any previous
#    installation of searx, morty and filtron services!

# utils/searx.sh
# --------------

# The setup of the SearXNG instance is done in the settings.yml
# (SEARXNG_SETTINGS_PATH).  Read the remarks in [1] carefully and don't forget to
# rebuild instance's environment (make buildenv) if needed.  The settings.yml
# file of an already installed instance is shown by::
#
#     $ ./utils/searx.sh --help
#     ---- SearXNG instance setup (already installed)
#       SEARXNG_SETTINGS_PATH : /etc/searxng/settings.yml
#       SEARX_SRC             : /usr/local/searx/searx-src
#
# [1] https://docs.searxng.org/admin/engines/settings.html

# utils/filtron.sh
# ----------------

# FILTRON_API="127.0.0.1:4005"
# FILTRON_LISTEN="127.0.0.1:4004"

# utils/morty.sh
# --------------

# morty listen address
# MORTY_LISTEN="127.0.0.1:3000"
# PUBLIC_URL_PATH_MORTY="/morty/"

# system services
# ---------------

# Common $HOME folder of the service accounts
# SERVICE_HOME_BASE="/usr/local"

# **experimental**: Set SERVICE_USER to run all services by one account, but be
# aware that removing discrete components might conflict!
# SERVICE_USER=searx
