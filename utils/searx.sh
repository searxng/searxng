#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# shellcheck disable=SC2001

# shellcheck source=utils/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
# shellcheck source=utils/brand.env
source "${REPO_ROOT}/utils/brand.env"

# ----------------------------------------------------------------------------
# config
# ----------------------------------------------------------------------------

PUBLIC_URL="${PUBLIC_URL:-${SEARXNG_URL}}"

SERVICE_NAME="searx"
SERVICE_USER="${SERVICE_USER:-${SERVICE_NAME}}"
SEARXNG_SETTINGS_PATH="/etc/searx/settings.yml"
SEARXNG_UWSGI_APP="searx.ini"

# ----------------------------------------------------------------------------
usage() {
# ----------------------------------------------------------------------------

    # shellcheck disable=SC1117
    cat <<EOF
usage::
  $(basename "$0") remove     all

remove all:    complete uninstall of SearXNG service

environment:
  PUBLIC_URL   : ${PUBLIC_URL}
EOF

    [[ -n ${1} ]] &&  err_msg "$1"
}

main() {

    local _usage="unknown or missing $1 command $2"

    case $1 in
        remove)
            rst_title "SearXNG (remove)" part
            sudo_or_exit
            case $2 in
                all) remove_all;;
                *) usage "$_usage"; exit 42;;
            esac ;;
        *) usage "unknown or missing command $1"; exit 42;;
    esac
}

remove_all() {
    rst_title "De-Install SearXNG (service)"

    rst_para "\
It goes without saying that this script can only be used to remove
installations that were installed with this script."

    if ! ask_yn "Do you really want to deinstall SearXNG?"; then
        return
    fi
    remove_searx_uwsgi
    drop_service_account "${SERVICE_USER}"
    remove_settings
    wait_key
    if service_is_available "${PUBLIC_URL}"; then
        MSG="** Don't forgett to remove your public site! (${PUBLIC_URL}) **" wait_key 10
    fi
}

remove_settings() {
    rst_title "remove SearXNG settings" section
    echo
    info_msg "delete ${SEARXNG_SETTINGS_PATH}"
    rm -f "${SEARXNG_SETTINGS_PATH}"
}

remove_searx_uwsgi() {
    rst_title "Remove SearXNG's uWSGI app (searxng.ini)" section
    echo
    uWSGI_remove_app "$SEARXNG_UWSGI_APP"
}


# ----------------------------------------------------------------------------
main "$@"
# ----------------------------------------------------------------------------
