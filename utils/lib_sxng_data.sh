#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later

data.help(){
    cat <<EOF
data.:
  all       : update searx/sxng_locales.py and searx/data/*
  traits    : update searx/data/engine_traits.json & searx/sxng_locales.py
  useragents: update searx/data/useragents.json with the most recent versions of Firefox
  locales   : update searx/data/locales.json from babel
EOF
}

data.all() {
    (   set -e

        data.traits
        data.useragents
	    data.locales

        build_msg DATA "update searx/data/osm_keys_tags.json"
        rye run python searxng_extra/update/update_osm_keys_tags.py
        build_msg DATA "update searx/data/ahmia_blacklist.txt"
        rye run python searxng_extra/update/update_ahmia_blacklist.py
        build_msg DATA "update searx/data/wikidata_units.json"
        rye run python searxng_extra/update/update_wikidata_units.py
        build_msg DATA "update searx/data/currencies.json"
        rye run python searxng_extra/update/update_currencies.py
        build_msg DATA "update searx/data/external_bangs.json"
        rye run python searxng_extra/update/update_external_bangs.py
        build_msg DATA "update searx/data/engine_descriptions.json"
        rye run python searxng_extra/update/update_engine_descriptions.py
    )
}


data.traits() {
    (   set -e
        build_msg DATA "update searx/data/engine_traits.json"
        rye run python searxng_extra/update/update_engine_traits.py
        build_msg ENGINES "update searx/sxng_locales.py"
    )
    dump_return $?
}

data.useragents() {
    build_msg DATA "update searx/data/useragents.json"
    rye run python searxng_extra/update/update_firefox_version.py
    dump_return $?
}

data.locales() {
    (   set -e
        build_msg DATA "update searx/data/locales.json"
        rye run python searxng_extra/update/update_locales.py
    )
    dump_return $?
}

docs.prebuild() {
    build_msg DOCS "build ${DOCS_BUILD}/includes"
    (
        set -e
        [ "$VERBOSE" = "1" ] && set -x
        mkdir -p "${DOCS_BUILD}/includes"
        ./utils/searxng.sh searxng.doc.rst >  "${DOCS_BUILD}/includes/searxng.rst"
        rye run searxng_extra/docs_prebuild
    )
    dump_return $?
}
