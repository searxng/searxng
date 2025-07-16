#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later

STATIC_BUILD_COMMIT="[build] /static"
STATIC_BUILT_PATHS=(
    'searx/templates/simple/icons.html'
    'searx/static/themes/simple'
    'client/simple/package-lock.json'
)

static.help() {
    cat <<EOF
static.build.:  ${STATIC_BUILD_COMMIT}
  commit    : build & commit /static folder
  drop      : drop last commit if it was previously done by static.build.commit
  restore   : git restore of the /static folder (after themes.all)
EOF
}

is.static.build.commit() {

    local commit_sha="$1"
    local commit_message
    local commit_files

    # check commit message
    commit_message=$(git show -s --format=%s "${commit_sha}")
    if [ "${commit_message}" != "${STATIC_BUILD_COMMIT}" ]; then
        err_msg "expecting commit message: '${STATIC_BUILD_COMMIT}'"
        err_msg "commit message of ${commit_sha} is: '${commit_message}'"
        return 1
    fi

    # check all files of the commit belongs to $STATIC_BUILT_PATHS
    commit_files=$(git diff-tree --no-commit-id --name-only -r "${commit_sha}")
    for i in "${STATIC_BUILT_PATHS[@]}"; do
        # remove files of ${STATIC_BUILT_PATHS}
        commit_files=$(echo "${commit_files}" | grep -v "^${i}")
    done

    if [ -n "${commit_files}" ]; then
        err_msg "commit ${commit_sha} contains files not a part of ${STATIC_BUILD_COMMIT}"
        echo "${commit_files}" | prefix_stdout "  "
        return 2
    fi
    return 0
}

static.build.drop() {
    # drop last commit if it was made by the static.build.commit command

    local last_commit_id
    local branch

    build_msg STATIC "drop last commit if it was previously done by static.build.commit"

    # get only last (option -n1) local commit not in remotes
    branch="$(git branch --show-current)"
    last_commit_id="$(git log -n1 "${branch}" --pretty=format:'%h' \
        --not --exclude="${branch}" --branches --remotes)"

    if [ -z "${last_commit_id}" ]; then
        err_msg "there are no local commits"
        return 1
    fi

    if ! is.static.build.commit "${last_commit_id}"; then
        return $?
    fi

    build_msg STATIC "drop last commit ${last_commit_id}"
    git reset --hard HEAD~1
}

static.build.commit() {
    # call the "static.build.drop" command, then "themes.all" then commit the
    # built files ($BUILT_PATHS).

    build_msg STATIC "build & commit /static files"

    # check for not committed files
    if [ -n "$(git diff --name-only)" ]; then
        err_msg "some files are not committed:"
        git diff --name-only | prefix_stdout "  "
        return 1
    fi

    # check for staged files
    if [ -n "$(git diff --name-only --cached)" ]; then
        err_msg "some files are staged:"
        git diff --name-only --cached | prefix_stdout "  "
        return 1
    fi

    # drop existing commit from previous build
    static.build.drop &>/dev/null

    (
        set -e
        # fix & build the themes
        themes.fix
        themes.lint
        themes.all

        # add build files
        for built_path in "${STATIC_BUILT_PATHS[@]}"; do
            git add -v "${built_path}"
        done

        # check if any file has been added (in case of no changes)
        if [ -z "$(git diff --name-only --cached)" ]; then
            build_msg STATIC "no changes applied / nothing to commit"
            return 0
        fi

        # check for modified files that are not staged
        if [ -n "$(git diff --name-only)" ]; then
            die 42 "themes.all has created files that are not in STATIC_BUILT_PATHS"
        fi
        git commit -m "${STATIC_BUILD_COMMIT}"
    )
}

static.build.restore() {
    build_msg STATIC "git-restore of the built files (/static)"
    git restore --staged "${STATIC_BUILT_PATHS[@]}"
    git restore --worktree "${STATIC_BUILT_PATHS[@]}"
}
