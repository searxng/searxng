#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later

themes.help() {
    cat <<EOF
themes.:
  all       : test & build all themes
  simple    : test & build simple theme
  advanced  : test & build advanced theme
  lint      : lint JS & CSS (LESS) files
  fix       : fix JS & CSS (LESS) files
  test      : test all themes
EOF
}

themes.all() {
    (
        set -e
        vite.simple.build
        vite.advanced.build
    )
    dump_return $?
}

themes.simple() {
    (
        set -e
        build_msg SIMPLE "theme: run build (simple)"
        vite.simple.build
    )
    dump_return $?
}

themes.simple.analyze() {
    (
        set -e
        build_msg SIMPLE "theme: run analyze (simple)"
        vite.simple.analyze
    )
    dump_return $?
}

themes.advanced() {
    (
        set -e
        build_msg ADVANCED "theme: run build (advanced)"
        vite.advanced.build
    )
    dump_return $?
}

themes.advanced.analyze() {
    (
        set -e
        build_msg ADVANCED "theme: run analyze (advanced)"
        vite.advanced.analyze
    )
    dump_return $?
}

themes.fix() {
    (
        set -e
        build_msg SIMPLE "theme: fix (simple)"
        vite.simple.fix
        build_msg ADVANCED "theme: fix (advanced)"
        vite.advanced.fix
    )
    dump_return $?
}

themes.lint() {
    (
        set -e
        build_msg SIMPLE "theme: lint (simple)"
        vite.simple.lint
        build_msg ADVANCED "theme: lint (advanced)"
        vite.advanced.lint
    )
    dump_return $?
}

themes.test() {
    (
        set -e
        # we run a build to test (in CI)
        build_msg SIMPLE "theme: run build (to test)"
        vite.simple.build
        build_msg ADVANCED "theme: run build (to test)"
        vite.advanced.build
    )
    dump_return $?
}
