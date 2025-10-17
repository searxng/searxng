#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later

test.help() {
    cat <<EOF
test.:
  yamllint  : lint YAML files (YAMLLINT_FILES)
  pylint    : lint ./searx, ./searxng_extra and ./tests
  pyright   : check Python types
  black     : check Python code format
  shfmt     : check Shell script code format
  unit      : run unit tests
  coverage  : run unit tests with coverage
  robot     : run robot test
  rst       : test .rst files incl. README.rst
  clean     : clean intermediate test stuff
EOF
}

if [ "$VERBOSE" = "1" ]; then
    TEST_NOSE2_VERBOSE="-vvv"
fi

test.yamllint() {
    build_msg TEST "[yamllint] $YAMLLINT_FILES"
    pyenv.cmd yamllint --strict --format parsable "${YAMLLINT_FILES[@]}"
    dump_return $?
}

test.pylint() {
    (
        set -e
        pyenv.activate
        PYLINT_OPTIONS="--rcfile .pylintrc"

        build_msg TEST "[pylint] ./searx/engines"
        # shellcheck disable=SC2086
        pylint ${PYLINT_OPTIONS} ${PYLINT_VERBOSE} \
            --additional-builtins="traits,supported_languages,language_aliases,logger,categories" \
            searx/engines

        build_msg TEST "[pylint] ./searx ./searxng_extra ./tests"
        # shellcheck disable=SC2086
        pylint ${PYLINT_OPTIONS} ${PYLINT_VERBOSE} \
            --ignore-paths=searx/engines \
            searx searx/searxng.msg \
            searxng_extra searxng_extra/docs_prebuild \
            tests
    )
    dump_return $?
}

test.pyright() {
    # For integration into your IDE (editor) use the basedpyright-langserver
    # (LSP) installed by 'pipx basedpyright' and read:
    #
    # - https://docs.basedpyright.com/latest/installation/ides/
    #
    # The $REPO_ROOT/pyrightconfig.json uses the virtualenv found in
    # $REPO_ROOT/local/py3 and create by a 'make pyenv'

    build_msg TEST "[basedpyright] static type check of python sources"
    LANG=C pyenv.cmd basedpyright
    # ignore exit value from basedpyright
    # dump_return $?
    return 0
}

test.pyright_modified() {
    build_msg TEST "[basedpyright] static type check of local modified files"
    local pyrigth_files=()
    readarray -t pyrigth_files < <(git status --porcelain | awk 'match($2,".py[i]*$") {print $2}')
    if [ ${#pyrigth_files[@]} -eq 0 ]; then
        echo "there are no locally modified python files that could be checked"
    else
        pyenv.cmd basedpyright --level warning "${pyrigth_files[@]}"
    fi
    # ignore exit value from basedpyright
    # dump_return $?
    return 0
}

test.black() {
    build_msg TEST "[black] $BLACK_TARGETS"
    pyenv.cmd black --check --diff "${BLACK_OPTIONS[@]}" "${BLACK_TARGETS[@]}"
    dump_return $?
}

test.shfmt() {
    build_msg TEST "[shfmt] ${SHFMT_SCRIPTS[*]}"
    go.tool shfmt --list --diff "${SHFMT_SCRIPTS[@]}"
    dump_return $?
}

test.unit() {
    build_msg TEST 'tests/unit'
    # shellcheck disable=SC2086
    pyenv.cmd python -m nose2 ${TEST_NOSE2_VERBOSE} -s tests/unit
    dump_return $?
}

test.coverage() {
    build_msg TEST 'unit test coverage'
    (
        set -e
        pyenv.activate
        # shellcheck disable=SC2086
        python -m nose2 ${TEST_NOSE2_VERBOSE} -C --log-capture --with-coverage --coverage searx -s tests/unit
        coverage report
        coverage html
    )
    dump_return $?
}

test.robot() {
    build_msg TEST 'robot'
    gecko.driver
    PYTHONPATH=. pyenv.cmd python -m tests.robot
    dump_return $?
}

test.rst() {
    build_msg TEST "[reST markup] ${RST_FILES[*]}"

    for rst in "${RST_FILES[@]}"; do
        pyenv.cmd rst2html --halt error "$rst" >/dev/null || die 42 "fix issue in $rst"
    done
}

test.themes() {
    build_msg TEST 'SearXNG themes'
    themes.test
    dump_return $?
}

test.pybabel() {
    TEST_BABEL_FOLDER="build/test/pybabel"
    build_msg TEST "[extract messages] pybabel"
    mkdir -p "${TEST_BABEL_FOLDER}"
    pyenv.cmd pybabel extract -F babel.cfg -o "${TEST_BABEL_FOLDER}/messages.pot" searx
}

test.clean() {
    build_msg CLEAN "test stuff"
    rm -rf geckodriver.log .coverage coverage/
    dump_return $?
}
