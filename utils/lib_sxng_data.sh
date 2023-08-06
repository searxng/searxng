#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later

data.help(){
    cat <<EOF
data.:
  all       : update searx/sxng_locales.py and searx/data/*
  traits    : update searx/data/engine_traits.json & searx/sxng_locales.py
  useragents: update searx/data/useragents.json with the most recent versions of Firefox
EOF
}

data.all() {
    (   set -e

        pyenv.activate
        data.traits
        data.useragents

        build_msg DATA "update searx/data/osm_keys_tags.json"
        pyenv.cmd python searxng_extra/update/update_osm_keys_tags.py
        build_msg DATA "update searx/data/ahmia_blacklist.txt"
        python searxng_extra/update/update_ahmia_blacklist.py
        build_msg DATA "update searx/data/wikidata_units.json"
        python searxng_extra/update/update_wikidata_units.py
        build_msg DATA "update searx/data/currencies.json"
        python searxng_extra/update/update_currencies.py
        build_msg DATA "update searx/data/external_bangs.json"
        python searxng_extra/update/update_external_bangs.py
        build_msg DATA "update searx/data/engine_descriptions.json"
        python searxng_extra/update/update_engine_descriptions.py
    )
}


data.traits() {
    (   set -e
        pyenv.activate
        build_msg DATA "update searx/data/engine_traits.json"
        python searxng_extra/update/update_engine_traits.py
        build_msg ENGINES "update searx/sxng_locales.py"
    )
    dump_return $?
}

data.useragents() {
    build_msg DATA "update searx/data/useragents.json"
    pyenv.cmd python searxng_extra/update/update_firefox_version.py
    dump_return $?
}

docs.prebuild() {
    build_msg DOCS "build ${DOCS_BUILD}/includes"
    (
        set -e
        [ "$VERBOSE" = "1" ] && set -x
        mkdir -p "${DOCS_BUILD}/includes"
        ./utils/searxng.sh searxng.doc.rst >  "${DOCS_BUILD}/includes/searxng.rst"
        pyenv.cmd searxng_extra/docs_prebuild
    )
    dump_return $?
}
