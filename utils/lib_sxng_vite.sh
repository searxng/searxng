#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later


vite.help(){
    cat <<EOF
vite.:  .. to be done ..
  simple.:
    build: build static files of the simple theme
    dev:   start development server
EOF
}

VITE_SIMPLE_THEME="${REPO_ROOT}/client/simple"
VITE_SIMPLE_DIST="${REPO_ROOT}/searx/static/themes/simple"

vite.simple.dev() {

    (   set -e
        build_msg SIMPLE "start server for FE development of: ${VITE_SIMPLE_THEME}"
        pushd "${VITE_SIMPLE_THEME}"
        npm install
        npm exec -- vite
        popd &> /dev/null
    )

}

vite.simple.build() {

    # build static files of the simple theme

    (   set -e
        build_msg SIMPLE "run build of theme from: ${VITE_SIMPLE_THEME}"

        pushd "${VITE_SIMPLE_THEME}"
        npm install
        npm run fix
        npm run icons.html
        npm run build

    )
}
