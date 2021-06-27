# -*- coding: utf-8; mode: sh -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# shellcheck shell=bash disable=SC2034
#
# This environment is used by ./utils scripts like filtron.sh or searx.sh.  The
# default values are *most flexible* and *best maintained*, you normally not
# need to change the defaults (except PUBLIC_URL).
#
# Before you change any value here you have to uninstall any previous
# installation.  Further is it recommended to backup your changes simply by
# adding them to you local brand (git branch)::
#
#     git add .config

# The public URL of the searx instance: PUBLIC_URL="https://mydomain.xy/searx"
# The default is taken from ./utils/brand.env.

PUBLIC_URL="${SEARX_URL}"

if [[ ${PUBLIC_URL} == "https://searx.me" ]]; then
    # hint: Linux containers do not have DNS entries, lets use IPs
    PUBLIC_URL="http://$(primary_ip)/searx"
fi

# searx.sh
# ---------

# SEARX_INTERNAL_HTTP="127.0.0.1:8888"
# SEARX_SETTINGS_TEMPLATE="${REPO_ROOT}/utils/templates/etc/searx/use_default_settings.yml"

# Only change, if you maintain a searx brand in your searx fork (GIT_URL) which
# is not hold by branch 'master'.  The branch has to be a local branch, in the
# repository from which you install (which is most often the case).  If you want
# to install branch 'foo', don't forget to run 'git branch foo origin/foo' once.
# GIT_BRANCH="${GIT_BRANCH:-master}"

# filtron.sh
# ----------

# FILTRON_API="127.0.0.1:4005"
# FILTRON_LISTEN="127.0.0.1:4004"
# FILTRON_TARGET="127.0.0.1:8888"
# FILTRON_RULES_TEMPLATE="${REPO_ROOT}/utils/templates/etc/searx/use_default_settings.yml"

# morty.sh
# --------

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
