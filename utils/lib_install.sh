#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later

# https://github.com/koalaman/shellcheck/issues/356#issuecomment-853515285
# shellcheck source=utils/lib.sh
. /dev/null

# Initialize installation procedures:
#
# - Modified source_dot_config function that
#   - loads .config.sh from an existing installation (at SEARX_SRC).
#   - initialize **SEARX_SRC_INIT_FILES**
# - functions like:
#   - install_log_searx_instance()
#   - install_searx_get_state()
#
# usage:
#   source lib_install.sh
#
# **Installation scripts**
#
# The utils/lib_install.sh is sourced by the installations scripts:
#
# - utils/searx.sh
# - utils/morty.sh
# - utils/filtron.sh
#
# If '${SEARX_SRC}/.config.sh' exists, the modified source_dot_config() function
# loads this configuration (instead of './.config.sh').

# **SEARX_SRC_INIT_FILES**
#
# Array of file names to sync into a installation at $SEARX_SRC.  The file names
# are relative to the $REPO_ROOT.  Set by function init_SEARX_SRC_INIT_FILES().
# Most often theses are files like:
# - .config.sh
# - searx/settings.yml
# - utils/brand.env
# - ...


SEARX_SRC_INIT_FILES=()

eval orig_"$(declare -f source_dot_config)"

source_dot_config() {

    # Modified source_dot_config function that
    # - loads .config.sh from an existing installation (at SEARX_SRC).
    # - initialize SEARX_SRC_INIT_FILES

    if [ -z "$eval_SEARX_SRC" ]; then
        export eval_SEARX_SRC='true'
        SEARX_SRC=$("${REPO_ROOT}/utils/searx.sh" --getenv SEARX_SRC)
        SEARX_PYENV=$("${REPO_ROOT}/utils/searx.sh" --getenv SEARX_PYENV)
        SEARXNG_SETTINGS_PATH=$("${REPO_ROOT}/utils/searx.sh" --getenv SEARXNG_SETTINGS_PATH)
        if [ ! -r "${SEARX_SRC}" ]; then
            info_msg "not yet cloned: ${SEARX_SRC}"
            orig_source_dot_config
            return 0
        fi
        info_msg "using instance at: ${SEARX_SRC}"

        # set and log DOT_CONFIG
        if [ -r "${SEARX_SRC}/.config.sh" ]; then
            info_msg "switching to ${SEARX_SRC}/.config.sh"
            DOT_CONFIG="${SEARX_SRC}/.config.sh"
        else
            info_msg "using local config: ${DOT_CONFIG}"
        fi
        init_SEARX_SRC_INIT_FILES
    fi
}

init_SEARX_SRC_INIT_FILES(){
    # init environment SEARX_SRC_INIT_FILES

    # Monitor modified files in the working-tree from the local repository, only
    # if the local file differs to the corresponding file in the instance.  Most
    # often theses are files like:
    #
    #  - .config.sh
    #  - searx/settings.yml
    #  - utils/brand.env
    #  - ...

    # keep list empty if there is no installation
    SEARX_SRC_INIT_FILES=()
    if [ ! -r "$SEARX_SRC" ]; then
        return 0
    fi

    local fname
    local msg=""
    local _prefix=""
    if [[ -n ${SUDO_USER} ]]; then
        _prefix="sudo -u ${SUDO_USER}"
    fi

    # Monitor local modified files from the repository, only if the local file
    # differs to the corresponding file in the instance

    while IFS= read -r fname; do
        if [ -z "$fname" ]; then
            continue
        fi
        if [ -r "${SEARX_SRC}/${fname}" ]; then
            # diff  "${REPO_ROOT}/${fname}" "${SEARX_SRC}/${fname}"
            if ! cmp --silent "${REPO_ROOT}/${fname}" "${SEARX_SRC}/${fname}"; then
                SEARX_SRC_INIT_FILES+=("${fname}")
                info_msg "local clone (workingtree), modified file: ./$fname"
                msg="to update use:  sudo -H ./utils/searx.sh install init-src"
            fi
        fi
    done <<< "$($_prefix git diff --name-only)"
    [ -n "$msg" ] &&  info_msg "$msg"
}

install_log_searx_instance() {

    echo -e "---- SearXNG instance setup ${_BBlue}(status: $(install_searx_get_state))${_creset}"
    echo -e "  SEARXNG_SETTINGS_PATH : ${_BBlue}${SEARXNG_SETTINGS_PATH}${_creset}"
    echo -e "  SEARX_PYENV         : ${_BBlue}${SEARX_PYENV}${_creset}"
    echo -e "  SEARX_SRC           : ${_BBlue}${SEARX_SRC:-none}${_creset}"
    echo -e "  SEARXNG_URL         : ${_BBlue}${SEARXNG_URL:-none}${_creset}"

    if in_container; then
        # SearXNG is listening on 127.0.0.1 and not available from outside container
        # in containers the service is listening on 0.0.0.0 (see lxc-searx.env)
        echo -e "---- container setup"
        echo -e "  ${_BBlack}HINT:${_creset} SearXNG only listen on loopback device" \
             "${_BBlack}inside${_creset} the container."
        for ip in $(global_IPs) ; do
            if [[ $ip =~ .*:.* ]]; then
                echo "  container (IPv6): [${ip#*|}]"
            else
                # IPv4:
                echo "  container (IPv4): ${ip#*|}"
            fi
        done
    fi
}

install_searx_get_state(){

    # usage: install_searx_get_state
    #
    # Prompts a string indicating the status of the installation procedure
    #
    # missing-searx-clone:
    #    There is no clone at ${SEARX_SRC}
    # missing-searx-pyenv:
    #    There is no pyenv in ${SEARX_PYENV}
    # installer-modified:
    #    There are files modified locally in the installer (clone),
    #    see ${SEARX_SRC_INIT_FILES} description.
    # python-installed:
    #    Scripts can be executed in instance's environment
    #    - user:  ${SERVICE_USER}
    #    - pyenv: ${SEARX_PYENV}

    if [ -f /etc/searx/settings.yml ]; then
        err_msg "settings.yml in /etc/searx/ is deprecated, move file to folder /etc/searxng/"
    fi

    if ! [ -r "${SEARX_SRC}" ]; then
        echo "missing-searx-clone"
        return
    fi
    if ! [ -f "${SEARX_PYENV}/bin/activate" ]; then
        echo "missing-searx-pyenv"
        return
    fi
    if ! [ -r "${SEARXNG_SETTINGS_PATH}" ]; then
        echo "missing-settings"
        return
    fi
    if ! [ ${#SEARX_SRC_INIT_FILES[*]} -eq 0 ]; then
        echo "installer-modified"
        return
    fi
    echo "python-installed"
}

# Initialization of the installation procedure
# --------------------------------------------

# shellcheck source=utils/brand.env
source "${REPO_ROOT}/utils/brand.env"

# SEARXNG_URL aka PUBLIC_URL: the public URL of the instance (e.g.
# "https://example.org/searx").  The value is taken from environment $SEARXNG_URL
# in ./utils/brand.env.  This variable is a empty string if server.base_url in
# the settings.yml is set to 'false'.

SEARXNG_URL="${SEARXNG_URL:-http://$(uname -n)}"
if in_container; then
    # hint: Linux containers do not have DNS entries, lets use IPs
    SEARXNG_URL="http://$(primary_ip)"
fi
PUBLIC_URL="${SEARXNG_URL}"

source_dot_config

# shellcheck source=utils/lxc-searx.env
source "${REPO_ROOT}/utils/lxc-searx.env"
in_container && lxc_set_suite_env
