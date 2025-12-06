#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later

weblate.help() {
    cat <<EOF
weblate.:
  push.translations: push translation changes from SearXNG to Weblate's counterpart
  to.translations: Update 'translations' branch with last additions from Weblate.
EOF
}

TRANSLATIONS_WORKTREE="$CACHE/translations"

weblate.translations.worktree() {

    # Create git worktree ${TRANSLATIONS_WORKTREE} and checkout branch
    # 'translations' from Weblate's counterpart (weblate) of the SearXNG
    # (origin).
    #
    #     remote weblate https://translate.codeberg.org/git/searxng/searxng/

    (
        set -e
        if ! git remote get-url weblate 2>/dev/null; then
            git remote add weblate https://translate.codeberg.org/git/searxng/searxng/
        fi
        if [ -d "${TRANSLATIONS_WORKTREE}" ]; then
            pushd "${TRANSLATIONS_WORKTREE}"
            git reset --hard HEAD
            git pull origin translations
            popd
        else
            mkdir -p "${TRANSLATIONS_WORKTREE}"
            git worktree add "${TRANSLATIONS_WORKTREE}" translations
        fi
    )
}

weblate.to.translations() {

    # Update 'translations' branch of SearXNG (origin) with last additions from
    # Weblate.

    # 1. Check if Weblate is locked, if not die with error message
    # 2. On Weblate's counterpart (weblate), pull master and translations branch
    #    from SearXNG (origin).
    # 3. Commit changes made in a Weblate object on Weblate's counterpart
    #    (weblate).
    # 4. In translations worktree, merge changes of branch 'translations' from
    #    remote 'weblate' and push it on branch 'translations' of 'origin'

    (
        set -e
        pyenv.activate
        if [ "$(wlc lock-status)" != "locked: True" ]; then
            die 1 "weblate must be locked, currently: $(wlc lock-status)"
        fi
        # weblate: commit pending changes
        wlc pull
        wlc commit

        # get the translations in a worktree
        weblate.translations.worktree

        pushd "${TRANSLATIONS_WORKTREE}"
        git remote update weblate
        git merge weblate/translations
        git push
        popd
    )
    dump_return $?
}

weblate.translations.commit() {

    # Update 'translations' branch of SearXNG (origin) with last additions from
    # Weblate.  Copy the changes to the master branch, compile translations and
    # create a commit in the local branch (master)

    local existing_commit_hash commit_body commit_message exitcode
    (
        set -e
        pyenv.activate
        # lock change on weblate
        wlc lock

        # get translations branch in git worktree (TRANSLATIONS_WORKTREE)
        weblate.translations.worktree

        pushd "${TRANSLATIONS_WORKTREE}"
        existing_commit_hash=$(git log -n1 --pretty=format:'%h')
        popd

        # pull weblate commits
        weblate.to.translations

        # copy the changes to the master branch
        cp -rv --preserve=mode,timestamps "${TRANSLATIONS_WORKTREE}/searx/translations" "searx"

        # compile translations
        build_msg BABEL 'compile translation catalogs into binary MO files'
        pybabel compile --statistics \
            -d "searx/translations"

        # update searx/data/translation_labels.json
        data.locales

        # git add/commit (no push)
        commit_body=$(
            cd "${TRANSLATIONS_WORKTREE}"
            git log --pretty=format:'%h - %as - %aN <%ae>' "${existing_commit_hash}..HEAD"
        )
        commit_message=$(echo -e "[l10n] update translations from Weblate\n\n${commit_body}")
        git add searx/translations
        git add searx/data/locales.json
        git commit -m "${commit_message}"
    )
    exitcode=$?
    ( # make sure to always unlock weblate
        set -e
        pyenv.cmd wlc unlock
    )
    dump_return $exitcode
}

weblate.push.translations() {

    # Push *translation changes* from SearXNG (origin) to Weblate's counterpart
    # (weblate).

    # In branch master of SearXNG (origin) check for meaningful changes in
    # folder 'searx/translations', commit changes on branch 'translations' and
    # at least, pull updated branches on Weblate's counterpart (weblate).

    # 1. Create git worktree ${TRANSLATIONS_WORKTREE} and checkout branch
    #    'translations' from remote 'weblate'.
    # 2. Stop if there is no meaningful change in the 'master' branch (origin),
    #    compared to the 'translations' branch (weblate), otherwise ...
    # 3. Update 'translations' branch of SearXNG (origin) with last additions
    #    from Weblate.
    # 5. Notify Weblate to pull updated 'master' & 'translations' branch.

    local messages_pot diff_messages_pot last_commit_hash last_commit_detail \
        exitcode
    messages_pot="${TRANSLATIONS_WORKTREE}/searx/translations/messages.pot"
    (
        set -e
        pyenv.activate
        # get translations branch in git worktree (TRANSLATIONS_WORKTREE)
        weblate.translations.worktree

        # update messages.pot in the master branch
        build_msg BABEL 'extract messages from source files and generate POT file'
        pybabel extract -F babel.cfg --project="SearXNG" --version="-" \
            -o "${messages_pot}" \
            "searx/"

        # stop if there is no meaningful change in the master branch
        diff_messages_pot=$(
            cd "${TRANSLATIONS_WORKTREE}"
            git diff -- "searx/translations/messages.pot"
        )
        if ! echo "$diff_messages_pot" | grep -qE "[\+\-](msgid|msgstr)"; then
            build_msg BABEL 'no changes detected, exiting'
            return 42
        fi
        return 0
    )
    exitcode=$?
    if [ "$exitcode" -eq 42 ]; then
        return 0
    fi
    if [ "$exitcode" -gt 0 ]; then
        return $exitcode
    fi
    (
        set -e
        pyenv.activate

        # lock change on weblate
        # weblate may add commit(s) since the call to "weblate.translations.worktree".
        # this is not a problem because after this line, "weblate.to.translations"
        # calls again "weblate.translations.worktree" which calls "git pull"
        wlc lock

        # save messages.pot in the translations branch for later
        pushd "${TRANSLATIONS_WORKTREE}"
        git stash push
        popd

        # merge weblate commits into the translations branch
        weblate.to.translations

        # restore messages.pot in the translations branch
        pushd "${TRANSLATIONS_WORKTREE}"
        git stash pop
        popd

        # update messages.po files in the master branch
        build_msg BABEL 'update existing message catalogs from POT file'
        pybabel update -N \
            -i "${messages_pot}" \
            -d "${TRANSLATIONS_WORKTREE}/searx/translations"

        # git add/commit/push
        last_commit_hash=$(git log -n1 --pretty=format:'%h')
        last_commit_detail=$(git log -n1 --pretty=format:'%h - %as - %aN <%ae>' "${last_commit_hash}")

        pushd "${TRANSLATIONS_WORKTREE}"
        git add searx/translations
        git commit \
            -m "[translations] update messages.pot and messages.po files" \
            -m "From ${last_commit_detail}"
        git push
        popd

        # notify weblate to pull updated master & translations branch
        wlc pull
    )
    exitcode=$?
    ( # make sure to always unlock weblate
        set -e
        pyenv.activate
        wlc unlock
    )
    dump_return $exitcode
}
