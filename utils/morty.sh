#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later

# shellcheck source=utils/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
# shellcheck source=utils/brand.env
source "${REPO_ROOT}/utils/brand.env"

# ----------------------------------------------------------------------------
# config
# ----------------------------------------------------------------------------

PUBLIC_URL="${PUBLIC_URL:-${SEARXNG_URL}}"

MORTY_LISTEN="${MORTY_LISTEN:-127.0.0.1:3000}"
PUBLIC_URL_PATH_MORTY="${PUBLIC_URL_PATH_MORTY:-/morty/}"
PUBLIC_URL_MORTY="${PUBLIC_URL_MORTY:-$(echo "$PUBLIC_URL" |  sed -e's,^\(.*://[^/]*\).*,\1,g')${PUBLIC_URL_PATH_MORTY}}"

SERVICE_NAME="morty"
SERVICE_USER="${SERVICE_USER:-${SERVICE_NAME}}"
SERVICE_SYSTEMD_UNIT="${SYSTEMD_UNITS}/${SERVICE_NAME}.service"

# Apache Settings

APACHE_MORTY_SITE="morty.conf"
NGINX_MORTY_SITE="morty.conf"

# ----------------------------------------------------------------------------
usage() {
# ----------------------------------------------------------------------------

    # shellcheck disable=SC1117
    cat <<EOF
usage::
  $(basename "$0") remove all
  $(basename "$0") apache remove
  $(basename "$0") nginx  remove

remove all     : drop all components of the morty service
apache remove  : drop apache site ${APACHE_MORTY_SITE}
nginx  remove  : drop nginx site ${NGINX_MORTY_SITE}

environment:
  PUBLIC_URL_MORTY   : ${PUBLIC_URL_MORTY}
EOF

    [[ -n ${1} ]] &&  err_msg "$1"
}

main() {
    local _usage="ERROR: unknown or missing $1 command $2"

    case $1 in
        -h|--help) usage; exit 0;;
        remove)
            sudo_or_exit
            case $2 in
                all) remove_all;;
                *) usage "$_usage"; exit 42;;
            esac ;;
        apache)
            sudo_or_exit
            case $2 in
                remove) remove_apache_site ;;
                *) usage "$_usage"; exit 42;;
            esac ;;
        nginx)
            sudo_or_exit
            case $2 in
                remove) remove_nginx_site ;;
                *) usage "$_usage"; exit 42;;
            esac ;;
        *) usage "ERROR: unknown or missing command $1"; exit 42;;
    esac
}


remove_all() {
    rst_title "De-Install $SERVICE_NAME (service)"

    rst_para "\
It goes without saying that this script can only be used to remove
installations that were installed with this script."

    if systemd_remove_service "${SERVICE_NAME}" "${SERVICE_SYSTEMD_UNIT}"; then
        drop_service_account "${SERVICE_USER}"
    fi
}


remove_apache_site() {

    rst_title "Remove Apache site $APACHE_MORTY_SITE"

    rst_para "\
This removes apache site ${APACHE_MORTY_SITE}."

    ! apache_is_installed && err_msg "Apache is not installed."

    if ! ask_yn "Do you really want to continue?" Yn; then
        return
    fi

    apache_remove_site "$APACHE_MORTY_SITE"
}

remove_nginx_site() {

    rst_title "Remove nginx site $NGINX_MORTY_SITE"

    rst_para "\
This removes nginx site ${NGINX_MORTY_SITE}."

    ! nginx_is_installed && err_msg "nginx is not installed."

    if ! ask_yn "Do you really want to continue?" Yn; then
        return
    fi

    nginx_remove_app "$NGINX_MORTY_SITE"

}

# ----------------------------------------------------------------------------
main "$@"
# ----------------------------------------------------------------------------
