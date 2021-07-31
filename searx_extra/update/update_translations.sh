#!/usr/bin/env bash
# -*- coding: utf-8; mode: sh indent-tabs-mode: nil -*-

# script to easily update translation language files

# add new language:
# pybabel init -i searx/translations/messages.pot -d searx/translations -l en

APP_DIR="searx"
TRANSLATIONS="${APP_DIR}/translations"
MESSAGES_POT="${TRANSLATIONS}/messages.pot"

get_sha256() {
    echo "$(grep "msgid" "${MESSAGES_POT}" | sort | sha256sum | cut -f1 -d\ )"
}

EXISTING_SHA="$(get_sha256)"

pybabel extract -F babel.cfg -o "${MESSAGES_POT}" "${APP_DIR}"

if [ "$(get_sha256)" = "${EXISTING_SHA}" ]; then
    echo '[!] no changes detected, exiting']
    exit 1
fi

pybabel update -N -i "${MESSAGES_POT}" -d "${TRANSLATIONS}"
echo '[!] update done, edit .po files if required and run pybabel compile -d searx/translations/'
exit 0
