#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later

data.help() {
    cat <<EOF
data.:
  all       : update zhensa/sxng_locales.py and zhensa/data/*
  traits    : update zhensa/data/engine_traits.json & zhensa/sxng_locales.py
  useragents: update zhensa/data/useragents.json with the most recent versions of Firefox
  locales   : update zhensa/data/locales.json from babel
  currencies: update zhensa/data/currencies.json from wikidata
EOF
}

data.all() {
    (
        set -e

        pyenv.activate
        data.traits
        data.useragents
        data.locales

        build_msg DATA "update zhensa/data/osm_keys_tags.json"
        pyenv.cmd python zhensa_extra/update/update_osm_keys_tags.py
        build_msg DATA "update zhensa/data/ahmia_blacklist.txt"
        python zhensa_extra/update/update_ahmia_blacklist.py
        build_msg DATA "update zhensa/data/wikidata_units.json"
        python zhensa_extra/update/update_wikidata_units.py
        build_msg DATA "update zhensa/data/currencies.json"
        python zhensa_extra/update/update_currencies.py
        build_msg DATA "update zhensa/data/external_bangs.json"
        python zhensa_extra/update/update_external_bangs.py
        build_msg DATA "update zhensa/data/engine_descriptions.json"
        python zhensa_extra/update/update_engine_descriptions.py
    )
}

data.traits() {
    (
        set -e
        pyenv.activate
        build_msg DATA "update zhensa/data/engine_traits.json"
        python zhensa_extra/update/update_engine_traits.py
        build_msg ENGINES "update zhensa/sxng_locales.py"
    )
    dump_return $?
}

data.useragents() {
    build_msg DATA "update zhensa/data/useragents.json"
    pyenv.cmd python zhensa_extra/update/update_firefox_version.py
    dump_return $?
}

data.locales() {
    (
        set -e
        pyenv.activate
        build_msg DATA "update zhensa/data/locales.json"
        python zhensa_extra/update/update_locales.py
    )
    dump_return $?
}

data.currencies() {
    (
        set -e
        pyenv.activate
        build_msg DATA "update zhensa/data/currencies.json"
        python zhensa_extra/update/update_currencies.py
    )
    dump_return $?
}
