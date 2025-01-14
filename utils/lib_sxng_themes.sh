#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later

declare _Blue
declare _creset

themes.help(){
    cat <<EOF
themes.:
  all       : build all themes
  live      : to get live builds of CSS & JS use 'LIVE_THEME=simple make run'
  simple.:    build simple theme
    test    : test simple theme
    pygments: build pygment's LESS files for simple theme
EOF
}

themes.all() {
    (   set -e
        themes.simple
    )
    dump_return $?
}

themes.live() {
    local LIVE_THEME="${LIVE_THEME:-${1}}"
    case "${LIVE_THEME}" in
        simple)
            theme="searx/static/themes/${LIVE_THEME}"
            ;;
        '')
            die_caller 42 "missing theme argument"
            ;;
        *)
            die_caller 42 "unknown theme '${LIVE_THEME}' // [simple]'"
            ;;
    esac
    build_msg GRUNT "theme: $1 (live build)"
    nodejs.ensure
    cd "${theme}"
    {
        npm install
        npm run watch
    } 2>&1 \
        | prefix_stdout "${_Blue}THEME ${1} ${_creset}  " \
        | grep -E --ignore-case --color 'error[s]?[:]? |warning[s]?[:]? |'
}

themes.simple() {
    (   set -e
	node.env
	themes.simple.pygments
    )
    build_msg GRUNT "theme: simple"
    npm --prefix searx/static/themes/simple run build
    dump_return $?
}

themes.simple.pygments() {
    build_msg PYGMENTS "searxng_extra/update/update_pygments.py"
    pyenv.cmd python searxng_extra/update/update_pygments.py \
	| prefix_stdout "${_Blue}PYGMENTS ${_creset} "
    if [ "${PIPESTATUS[0]}" -ne "0" ]; then
        build_msg PYGMENTS "building LESS files for pygments failed"
        return 1
    fi
    return 0
}


themes.simple.test() {
    build_msg TEST "theme: simple"
    node.env
    npm --prefix searx/static/themes/simple install
    npm --prefix searx/static/themes/simple run test
    dump_return $?
}
