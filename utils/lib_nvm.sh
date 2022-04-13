#!/usr/bin/env bash
# -*- coding: utf-8; mode: sh indent-tabs-mode: nil -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Tools to install and maintain NVM versions manager for Node.js
#
# [1] https://github.com/nvm-sh/nvm

# https://github.com/koalaman/shellcheck/issues/356#issuecomment-853515285
# shellcheck source=utils/lib.sh
. /dev/null

declare main_cmd

# configure nvm environment
# -------------------------

NVM_LOCAL_FOLDER=.nvm

[[ -z "${NVM_GIT_URL}" ]] &&  NVM_GIT_URL="https://github.com/nvm-sh/nvm.git"
[[ -z "${NVM_MIN_NODE_VER}" ]] && NVM_MIN_NODE_VER="16.13.0"

# initalize nvm environment
# -------------------------

nvm.env() {
    source "${NVM_DIR}/nvm.sh"
    source "${NVM_DIR}/bash_completion"
    [ "$VERBOSE" = "1" ] && info_msg "sourced NVM environment from ${NVM_DIR}"
}

nvm.is_installed() {
    # is true if NVM is installed / in $HOME or even in <repo-root>/.nvm
    [[ -f "${NVM_DIR}/nvm.sh" ]]
}

if [[ -z "${NVM_DIR}" ]]; then
    # nvm is not pre-intalled in $HOME.  Prepare for using nvm from <repo-root>
    NVM_DIR="$(git rev-parse --show-toplevel)/${NVM_LOCAL_FOLDER}"
fi
export NVM_DIR

if nvm.is_installed; then
    nvm.env
else
    # if nvm is not installed, use this function as a wrapper
    nvm() {
        nvm.ensure
        nvm "$@"
    }
fi

# implement nvm functions
# -----------------------

nvm.is_local() {
    # is true if NVM is installed in <repo-root>/.nvm
    [ "${NVM_DIR}" = "$(git rev-parse --show-toplevel)/${NVM_LOCAL_FOLDER}" ]
}

nvm.min_node() {

    # usage:  nvm.min_node 16.3.0
    #
    # Is true if minimal Node.js version is installed.

    local min_v
    local node_v
    local higher_v

    if ! command -v node >/dev/null; then
        warn_msg "Node.js is not yet installed"
        return 42
    fi

    min_v="${1}"
    node_v="$(node --version)"
    node_v="${node_v:1}" # remove 'v' from 'v16.3.0'
    if ! [ "${min_v}" = "${node_v}" ]; then
        higher_v="$(echo -e "$min_v\n${node_v}" | sort -Vr | head -1)"
        if [ "${min_v}" = "${higher_v}" ]; then
            return 42
        fi
    fi
}

# implement nvm command line
# --------------------------

nvm.help() {
    cat <<EOF
nvm.: use nvm (without dot) to execute nvm commands directly
  install   : install NVM locally at $(git rev-parse --show-toplevel)/${NVM_LOCAL_FOLDER}
  clean     : remove NVM installation
  status    : prompt some status informations about nvm & node
  nodejs    : install Node.js latest LTS
  cmd ...   : run command ... in NVM environment
  bash      : start bash interpreter with NVM environment sourced
EOF
}

nvm.install() {
    local NVM_VERSION_TAG
    info_msg "install (update) NVM at ${NVM_DIR}"
    if [[ -d "${NVM_DIR}" ]] ; then
        info_msg "already cloned at: ${NVM_DIR}"
        pushd "${NVM_DIR}" &> /dev/null
        git fetch --all | prefix_stdout "  ${_Yellow}||${_creset} "
    else
        info_msg "clone: ${NVM_GIT_URL}"
        git clone "${NVM_GIT_URL}" "${NVM_DIR}" 2>&1 | prefix_stdout "  ${_Yellow}||${_creset} "
        pushd "${NVM_DIR}" &> /dev/null
        git config --local advice.detachedHead false
    fi
    NVM_VERSION_TAG="$(git rev-list --tags --max-count=1)"
    NVM_VERSION_TAG="$(git describe --abbrev=0 --tags --match "v[0-9]*" "${NVM_VERSION_TAG}")"
    info_msg "checkout ${NVM_VERSION_TAG}"
    git checkout "${NVM_VERSION_TAG}" 2>&1 | prefix_stdout "  ${_Yellow}||${_creset} "
    popd &> /dev/null
    if [ -f "${REPO_ROOT}/.nvm_packages" ]; then
        cp "${REPO_ROOT}/.nvm_packages" "${NVM_DIR}/default-packages"
    fi
    nvm.env
}

nvm.clean() {
    if ! nvm.is_installed; then
        build_msg CLEAN "[NVM] not installed"
        return
    fi
    if ! nvm.is_local; then
        build_msg CLEAN "[NVM] can't remove nvm from ${NVM_DIR}"
        return
    fi
    if [ -n "${NVM_DIR}" ]; then
        build_msg CLEAN "[NVM] drop $(realpath --relative-to=. "${NVM_DIR}")/"
        rm -rf "${NVM_DIR}"
    fi
}

nvm.status() {
    if command -v node >/dev/null; then
        info_msg "Node.js is installed at $(command -v node)"
        info_msg "Node.js is version $(node --version)"
        if ! nvm.min_node "${NVM_MIN_NODE_VER}"; then
            warn_msg "minimal Node.js version is ${NVM_MIN_NODE_VER}"
        fi
    else
        warn_msg "Node.js is mot installed"
    fi
    if command -v npm >/dev/null; then
        info_msg "npm is installed at $(command -v npm)"
        info_msg "npm is version $(npm --version)"
    else
        warn_msg "npm is not installed"
    fi
    if nvm.is_installed; then
        info_msg "NVM is installed at ${NVM_DIR}"
    else
        warn_msg "NVM is not installed"
        info_msg "to install NVM and Node.js (LTS) use: ${main_cmd} nvm.nodejs"
    fi
}

nvm.nodejs() {
    nvm install
    nvm.status
}

nvm.bash() {
    nvm.ensure
    bash --init-file <(cat "${NVM_DIR}/nvm.sh" "${NVM_DIR}/bash_completion")
}

nvm.cmd() {
    nvm.ensure
    "$@"
}

nvm.ensure() {
    if ! nvm.is_installed; then
        nvm.install
    fi
}
