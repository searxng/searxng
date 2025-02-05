#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later

themes.help(){
    cat <<EOF
themes.:
  all       : test & build all themes
  test      : test all themes
  fix       : fix JS & CSS (LESS)
EOF
}

themes.all() {
    (   set -e
        build_msg SIMPLE "theme: run build"
        vite.simple.build
    )
    dump_return $?
}

themes.fix() {
    (   set -e
        build_msg SIMPLE "theme: fix"
        vite.simple.fix
    )
    dump_return $?
}

themes.test() {
    (   set -e
        # we run a build to test (in CI)
        build_msg SIMPLE "theme: run build (to test)"
        vite.simple.build
    )
    dump_return $?
}
