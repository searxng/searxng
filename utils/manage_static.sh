#!/usr/bin/env bash
# -*- coding: utf-8; mode: sh indent-tabs-mode: nil -*-
# SPDX-License-Identifier: AGPL-3.0-or-later

BUILD_COMMIT_MESSAGE="Static build"

BUILT_PATHS=(
    searx/static/themes/oscar/css
    searx/static/themes/oscar/js
    searx/static/themes/oscar/src/generated/pygments-logicodev.less
    searx/static/themes/oscar/src/generated/pygments-pointhi.less
    searx/static/themes/simple/css
    searx/static/themes/simple/js
    searx/static/themes/simple/src/generated/pygments.less
)

CURRENT_BRANCH="$(git branch --show-current)"
STAGED_FILES=$(git diff --name-only --cached)

git_log_current_branch() {
    git log "heads/${CURRENT_BRANCH}" --not --exclude="${CURRENT_BRANCH}" --branches --remotes --pretty=format:"%h"
}

is.build.commit() {
    COMMIT_SHA=$1
    # check commit message
    COMMIT_MESSAGE=$(git show -s --format=%s ${COMMIT_SHA})
    if [ "${COMMIT_MESSAGE}" != "${BUILD_COMMIT_MESSAGE}" ]; then
        echo "Commit message of ${COMMIT_SHA} is '${COMMIT_MESSAGE}'"
        return 1
    fi

    # check all files of the commit belongs to $BUILT_PATHS
    COMMIT_FILES=$(git diff-tree --no-commit-id --name-only -r "${COMMIT_SHA}")
    for i in ${BUILT_PATHS[*]}; do
        # remove files of ${BUILT_PATHS}
        COMMIT_FILES=$(echo "${COMMIT_FILES}" | grep -v "^${i}")
    done
    if [ -n "${COMMIT_FILES}" ]; then
        echo "Commit $1 contains files that were not build: ${COMMIT_FILES}"
        return 2
    fi
    return 0
}

static.build.commit.drop() {
    LAST_COMMIT_ID=$(git_log_current_branch | head -1)

    if [ -z "${LAST_COMMIT_ID}" ]; then
        echo "Empty branch"
        return 1
    fi

    is.build.commit "${LAST_COMMIT_ID}"
    if [ $? -ne 0 ]; then
        return $?
    fi
    echo "Drop last commit ${LAST_COMMIT_ID}"
    git reset --hard HEAD~1
}

static.build.commit() {
    # check for not commited files
    NOT_COMMITED_FILES="$(git diff --name-only)"
    if [ -n "${NOT_COMMITED_FILES}" ]; then
        echo "Some files are not commited:"
        echo "${NOT_COMMITED_FILES}"
        return 1
    fi

    # check for staged files
    if [ -n "${STAGED_FILES}" ]; then
        echo "Some files are staged:"
        echo "${STAGED_FILES}"
        return 1
    fi

    # drop existing commit
    static.commit.drop
    if [ $? -ne 0 ]; then
        return $?
    fi

    (
        set -e
        # build the themes
        make themes.all

        # add build files
        for built_path in ${BUILT_PATHS[@]}; do
            git add -v "${built_path}"
        done

        # check for modified files that are not staged
        if [ -n "$(git diff --name-only)" ]; then
            echo "make themes.all has created files that are not in BUILT_PATHS"
            return 2
        fi

        #
        git commit -m "Static build"
    )
}

static.git.restore.staged() {
    for i in ${BUILT_PATHS[*]}; do
        STAGED_FILES_FOR_I=$(echo "${STAGED_FILES}" | grep "^${i}")
        if [ -n "${STAGED_FILES_FOR_I}" ]; then
            git restore --staged ${STAGED_FILES_FOR_I}
        fi
    done
}

static.git.restore() {
    static.git.restore.staged

    NOT_COMMITED_FILES="$(git diff --name-only)"
    for i in ${BUILT_PATHS[*]}; do
        NOT_COMMITED_FILES_FOR_I=$(echo "${NOT_COMMITED_FILES}" | grep "^${i}")
        if [ -n "${NOT_COMMITED_FILES_FOR_I}" ]; then
            git restore ${NOT_COMMITED_FILES_FOR_I}
        fi
    done
}

main() {
    case $1 in
        static.build.commit.drop)
            # drop last commit if it was made by the "commit" command
            static.build.commit.drop
            ;;
        static.build.commit)
            # call the "static.build.commit.drop" command,
            # then "make themes.all"
            # then commit the built files ($BUILT_PATHS).
            static.build.commit
            ;;
        static.git.restore.staged)
            # after "git add ."
            # remove the built files
            # so only the source are commited
            static.git.restore.staged
            ;;
        static.git.restore)
            # "git restore" of the built files.
            static.git.restore
            ;;
    esac
}

main "$@"
