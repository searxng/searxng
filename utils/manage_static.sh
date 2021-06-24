#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later

BUILD_COMMIT_MESSAGE="[build] /static"

BUILT_PATHS=(
    searx/static/themes/oscar/css
    searx/static/themes/oscar/js
    searx/static/themes/oscar/src/generated/pygments-logicodev.less
    searx/static/themes/oscar/src/generated/pygments-pointhi.less
    searx/static/themes/simple/css
    searx/static/themes/simple/js
    searx/static/themes/simple/src/generated/pygments.less
)

git_log_current_branch() {
    local branch
    branch="$(git branch --show-current)"
    git log "${branch}" --pretty=format:'%h' \
        --not --exclude="${branch}" --branches --remotes
}

is.build.commit() {
    local commit_sha="$1"
    local commit_message
    local commit_files

    # check commit message
    commit_message=$(git show -s --format=%s "${commit_sha}")
    if [ "${commit_message}" != "${BUILD_COMMIT_MESSAGE}" ]; then
        echo "Commit message of ${commit_sha} is '${commit_message}'"
        return 1
    fi

    # check all files of the commit belongs to $BUILT_PATHS
    commit_files=$(git diff-tree --no-commit-id --name-only -r "${commit_sha}")
    for i in ${BUILT_PATHS[*]}; do
        # remove files of ${BUILT_PATHS}
        commit_files=$(echo "${commit_files}" | grep -v "^${i}")
    done

    if [ -n "${commit_files}" ]; then
        echo "Commit $1 contains files that were not build: ${commit_files}"
        return 2
    fi
    return 0
}

static.build.commit.drop() {
    local last_commit_id
    last_commit_id=$(git_log_current_branch | head -1)

    if [ -z "${last_commit_id}" ]; then
        echo "Empty branch"
        return 1
    fi

    if ! is.build.commit "${last_commit_id}"; then
        return $?
    fi
    echo "Drop last commit ${last_commit_id}"
    git reset --hard HEAD~1
}

static.build.commit() {
    local staged_files

    # check for not commited files
    if [ -n "$(git diff --name-only)" ]; then
        echo "Some files are not commited:"
        echo "${NOT_COMMITED_FILES}"
        return 1
    fi

    staged_files=$(git diff --name-only --cached)

    # check for staged files
    if [ -n "${staged_files}" ]; then
        echo "Some files are staged:"
        echo "${staged_files}"
        return 1
    fi

    # drop existing commit
    if static.commit.drop; then
        return $?
    fi

    (
        set -e
        # build the themes
        make themes.all

        # add build files
        for built_path in "${BUILT_PATHS[@]}"; do
            git add -v "${built_path}"
        done

        # check for modified files that are not staged
        if [ -n "$(git diff --name-only)" ]; then
            echo "make themes.all has created files that are not in BUILT_PATHS"
            return 2
        fi
        git commit -m "${BUILD_COMMIT_MESSAGE}"
    )
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
            git restore --staged "${BUILT_PATHS[@]}"
            ;;
        static.git.restore)
            # "git restore" of the built files.
            git restore --worktree --staged "${BUILT_PATHS[@]}"
            ;;
    esac
}

main "$@"
