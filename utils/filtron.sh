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

FILTRON_ETC="/etc/filtron"

SERVICE_NAME="filtron"
SERVICE_USER="${SERVICE_USER:-${SERVICE_NAME}}"
SERVICE_SYSTEMD_UNIT="${SYSTEMD_UNITS}/${SERVICE_NAME}.service"

APACHE_FILTRON_SITE="searx.conf"
NGINX_FILTRON_SITE="searx.conf"

# ----------------------------------------------------------------------------
usage() {
# ----------------------------------------------------------------------------

    # shellcheck disable=SC1117
    cat <<EOF
usage::
  $(basename "$0") remove all
  $(basename "$0") apache remove
  $(basename "$0") nginx  remove

remove all     : drop all components of the filtron service
apache remove  : drop apache site ${APACHE_FILTRON_SITE}
nginx  remove  : drop nginx site ${NGINX_FILTRON_SITE}

environment:
  PUBLIC_URL   : ${PUBLIC_URL}
EOF

    [[ -n ${1} ]] &&  err_msg "$1"
}

main() {
    local _usage="unknown or missing $1 command $2"

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
        *) usage "unknown or missing command $1"; exit 42;;
    esac
}

remove_all() {
    rst_title "De-Install $SERVICE_NAME (service)"

    rst_para "\
It goes without saying that this script can only be used to remove
installations that were installed with this script."

    if ! systemd_remove_service "${SERVICE_NAME}" "${SERVICE_SYSTEMD_UNIT}"; then
        return 42
    fi
    drop_service_account "${SERVICE_USER}"
    rm -r "$FILTRON_ETC" 2>&1 | prefix_stdout
    if service_is_available "${PUBLIC_URL}"; then
        MSG="** Don't forget to remove your public site! (${PUBLIC_URL}) **" wait_key 10
    fi
}

remove_apache_site() {

    rst_title "Remove Apache site $APACHE_FILTRON_SITE"

    rst_para "\
This removes apache site ${APACHE_FILTRON_SITE}."

    ! apache_is_installed && err_msg "Apache is not installed."

    if ! ask_yn "Do you really want to continue?" Yn; then
        return
    fi

    apache_remove_site "$APACHE_FILTRON_SITE"

}

remove_nginx_site() {

    rst_title "Remove nginx site $NGINX_FILTRON_SITE"

    rst_para "\
This removes nginx site ${NGINX_FILTRON_SITE}."

    ! nginx_is_installed && err_msg "nginx is not installed."

    if ! ask_yn "Do you really want to continue?" Yn; then
        return
    fi

    nginx_remove_app "$FILTRON_FILTRON_SITE"

}

# ----------------------------------------------------------------------------
main "$@"
# ----------------------------------------------------------------------------
