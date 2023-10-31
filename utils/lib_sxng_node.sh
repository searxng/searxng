#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later

export NODE_MINIMUM_VERSION="16.13.0"

node.help(){
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
    (   set -e
        build_msg INSTALL "./searx/static/themes/simple/package.json"
        build_msg INSTALL "./searx/static/themes/kvanDark/package.json"
        npm --prefix searx/static/themes/simple install
        npm --prefix searx/static/themes/kvanDark install
    )
    dump_return $?
}

node.env.dev() {
    nodejs.ensure
    build_msg INSTALL "./package.json: developer and CI tools"
    npm install
}

node.clean() {
    if ! required_commands npm 2>/dev/null; then
        build_msg CLEAN "npm is not installed / ignore npm dependencies"
        return 0
    fi
    build_msg CLEAN "themes -- locally installed npm dependencies"
    (   set -e
        npm --prefix searx/static/themes/simple run clean
        npm --prefix searx/static/themes/kvanDark run clean
    )
    build_msg CLEAN "locally installed developer and CI tools"
    (   set -e
        npm --prefix . run clean
    )
    dump_return $?
}
