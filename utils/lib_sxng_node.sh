#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later

declare _Blue
declare _creset

export NODE_MINIMUM_VERSION="24.3.0"

node.help() {
    cat <<EOF
node.:
  env       : download & install SearXNG's npm dependencies locally
  env.dev   : download & install developer and CI tools
  clean     : drop locally npm installations
EOF
}

nodejs.ensure() {
    if ! nvm.min_node "${NODE_MINIMUM_VERSION}"; then
        info_msg "install Node.js by NVM"
        nvm.nodejs
    fi
}

node.env() {
    nodejs.ensure
    (
        set -e
        build_msg INSTALL "[npm] ./client/simple/package.json"
        npm --prefix client/simple install
    )
    dump_return $?
}

node.env.dev() {
    nodejs.ensure
    build_msg INSTALL "[npm] ./package.json: developer and CI tools"
    npm install
}

node.clean() {
    if ! required_commands npm 2>/dev/null; then
        build_msg CLEAN "npm is not installed / ignore npm dependencies"
        return 0
    fi
    build_msg CLEAN "themes -- locally installed npm dependencies"
    (
        set -e
        npm --prefix client/simple run clean |
            prefix_stdout "${_Blue}CLEAN    ${_creset} "
        if [ "${PIPESTATUS[0]}" -ne "0" ]; then
            return 1
        fi
    )
    build_msg CLEAN "locally installed developer and CI tools"
    (
        set -e
        npm --prefix . run clean |
            prefix_stdout "${_Blue}CLEAN    ${_creset} "
        if [ "${PIPESTATUS[0]}" -ne "0" ]; then
            return 1
        fi
    )
    dump_return $?
}
