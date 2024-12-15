#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later

declare _Blue
declare _creset

themes.help(){
    cat <<EOF
themes.:
  all       : test & build all themes
  test      : test all themes
  fix       : fix JS & CSS (LESS)
  live      : to get live builds of CSS & JS use: LIVE_THEME=simple make run
  simple.:    test & build simple theme ..
    pygments: build pygment's LESS files for simple theme
    test    : test simple theme
    fix     : fix JS & CSS (LESS) of the simple theme
EOF
}

themes.all() {
    (   set -e
        node.env
        themes.simple
    )
    dump_return $?
}

themes.fix() {
    (   set -e
        node.env
        themes.simple.fix
    )
    dump_return $?
}

themes.test() {
    (   set -e
        node.env
        themes.simple.test
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
            die 42 "missing theme argument"
            ;;
        *)
            die 42 "unknown theme '${LIVE_THEME}' // [simple]'"
            ;;
    esac
    build_msg SIMPLE "theme: $1 (live build)"
    node.env
    themes.simple.pygments
    cd "${theme}"
    {
        npm run watch
    } # 2>&1 \
      #       | prefix_stdout "${_Blue}THEME ${1} ${_creset}  " \
      #       | grep -E --ignore-case --color 'error[s]?[:]? |warning[s]?[:]? |'
}

themes.simple() {
    (   set -e
        themes.simple.pygments
        build_msg SIMPLE "theme: run build"
        # "run build" includes tests from eslint and stylelint
        npm --prefix searx/static/themes/simple run build
    )
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

themes.simple.fix() {
    build_msg SIMPLE "theme: fix"
    npm --prefix searx/static/themes/simple run fix
    dump_return $?
}

themes.simple.test() {
    build_msg SIMPLE "theme: run test"
    npm --prefix searx/static/themes/simple run test
    dump_return $?
}
