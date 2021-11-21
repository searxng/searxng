#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# shellcheck disable=SC2001

# shellcheck source=utils/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
# shellcheck source=utils/lib_go.sh
source "${REPO_ROOT}/utils/lib_go.sh"
# shellcheck source=utils/lib_install.sh
source "${REPO_ROOT}/utils/lib_install.sh"

# ----------------------------------------------------------------------------
# config
# ----------------------------------------------------------------------------

PUBLIC_HOST="${PUBLIC_HOST:-$(echo "$PUBLIC_URL" | sed -e 's/[^/]*\/\/\([^@]*@\)\?\([^:/]*\).*/\2/')}"

FILTRON_URL_PATH="${FILTRON_URL_PATH:-$(echo "${PUBLIC_URL}" \
| sed -e 's,^.*://[^/]*\(/.*\),\1,g')}"
[[ "${FILTRON_URL_PATH}" == "${PUBLIC_URL}" ]] && FILTRON_URL_PATH=/

FILTRON_ETC="/etc/filtron"
FILTRON_RULES="$FILTRON_ETC/rules.json"
FILTRON_RULES_TEMPLATE="${FILTRON_RULES_TEMPLATE:-${REPO_ROOT}/utils/templates/etc/filtron/rules.json}"

FILTRON_API="${FILTRON_API:-127.0.0.1:4005}"
FILTRON_LISTEN="${FILTRON_LISTEN:-127.0.0.1:4004}"

# The filtron target is the SearXNG installation, listenning on server.port at
# server.bind_address.  The default of FILTRON_TARGET is taken from the YAML
# configuration, do not change this value without reinstalling the entire
# SearXNG suite including filtron & morty.
FILTRON_TARGET="${SEARXNG_BIND_ADDRESS}:${SEARXNG_PORT}"

SERVICE_NAME="filtron"
SERVICE_USER="${SERVICE_USER:-${SERVICE_NAME}}"
SERVICE_HOME_BASE="${SERVICE_HOME_BASE:-/usr/local}"
SERVICE_HOME="${SERVICE_HOME_BASE}/${SERVICE_USER}"
SERVICE_SYSTEMD_UNIT="${SYSTEMD_UNITS}/${SERVICE_NAME}.service"
# shellcheck disable=SC2034
SERVICE_GROUP="${SERVICE_USER}"

# shellcheck disable=SC2034
SERVICE_GROUP="${SERVICE_USER}"

GO_ENV="${SERVICE_HOME}/.go_env"
GO_VERSION="go1.17.2"

APACHE_FILTRON_SITE="searxng.conf"
NGINX_FILTRON_SITE="searxng.conf"

# shellcheck disable=SC2034
CONFIG_FILES=(
    "${FILTRON_RULES}"
    "${SERVICE_SYSTEMD_UNIT}"
)

# ----------------------------------------------------------------------------
usage() {
# ----------------------------------------------------------------------------

    # shellcheck disable=SC1117
    cat <<EOF
usage::
  $(basename "$0") shell
  $(basename "$0") install    [all|user|rules]
  $(basename "$0") reinstall  all
  $(basename "$0") update     [filtron]
  $(basename "$0") remove     [all]
  $(basename "$0") activate   [service]
  $(basename "$0") deactivate [service]
  $(basename "$0") inspect    [service]
  $(basename "$0") option     [debug-on|debug-off]
  $(basename "$0") apache     [install|remove]
  $(basename "$0") nginx      [install|remove]

shell
  start interactive shell from user ${SERVICE_USER}
install / remove
  :all:        complete setup of filtron service
  :user:       add/remove service user '$SERVICE_USER' ($SERVICE_HOME)
  :rules:      reinstall filtron rules $FILTRON_RULES
install
  :check:      check the filtron installation
reinstall:
  :all:        runs 'install/remove all'
update filtron
  Update filtron installation ($SERVICE_HOME)
activate service
  activate and start service daemon (systemd unit)
deactivate service
  stop and deactivate service daemon (systemd unit)
inspect service
  show service status and log
option
  set one of the available options
apache (${PUBLIC_URL})
  :install: apache site with a reverse proxy (ProxyPass)
  :remove:  apache site ${APACHE_FILTRON_SITE}
nginx (${PUBLIC_URL})
  :install: nginx site with a reverse proxy (ProxyPass)
  :remove:  nginx site ${NGINX_FILTRON_SITE}
filtron rules: ${FILTRON_RULES_TEMPLATE}
---- sourced ${DOT_CONFIG} :
  SERVICE_USER        : ${SERVICE_USER}
  SERVICE_HOME        : ${SERVICE_HOME}
  FILTRON_TARGET      : ${FILTRON_TARGET}
  FILTRON_API         : ${FILTRON_API}
  FILTRON_LISTEN      : ${FILTRON_LISTEN}
  FILTRON_URL_PATH    : ${FILTRON_URL_PATH}
EOF

    install_log_searx_instance
    [[ -n ${1} ]] &&  err_msg "$1"
}

main() {
    required_commands \
        sudo install git wget curl \
        || exit

    local _usage="unknown or missing $1 command $2"

    case $1 in
        --getenv)  var="$2"; echo "${!var}"; exit 0;;
        -h|--help) usage; exit 0;;

        shell)
            sudo_or_exit
            interactive_shell "${SERVICE_USER}"
            ;;
        inspect)
            case $2 in
                service)
                    sudo_or_exit
                    inspect_service
                    ;;
                *) usage "$_usage"; exit 42;;
            esac ;;
        reinstall)
            rst_title "re-install $SERVICE_NAME" part
            sudo_or_exit
            case $2 in
                all)
                    remove_all
                    install_all
                    ;;
                *) usage "$_usage"; exit 42;;
            esac ;;
        install)
            rst_title "$SERVICE_NAME" part
            sudo_or_exit
            case $2 in
                check)
                    rst_title "Check filtron installation" part
                    install_check
                    ;;
                all) install_all ;;
                user) assert_user ;;
                rules)
                    install_rules
                    systemd_restart_service "${SERVICE_NAME}"
                    ;;
                *) usage "$_usage"; exit 42;;
            esac ;;
        update)
            sudo_or_exit
            case $2 in
                filtron) update_filtron ;;
                *) usage "$_usage"; exit 42;;
            esac ;;
        remove)
            sudo_or_exit
            case $2 in
                all) remove_all;;
                user) drop_service_account "${SERVICE_USER}" ;;
                *) usage "$_usage"; exit 42;;
            esac ;;
        activate)
            sudo_or_exit
            case $2 in
                service)  systemd_activate_service "${SERVICE_NAME}" ;;
                *) usage "$_usage"; exit 42;;
            esac ;;
        deactivate)
            sudo_or_exit
            case $2 in
                service)  systemd_deactivate_service "${SERVICE_NAME}" ;;
                *) usage "$_usage"; exit 42;;
            esac ;;
        apache)
            sudo_or_exit
            case $2 in
                install) install_apache_site ;;
                remove) remove_apache_site ;;
                *) usage "$_usage"; exit 42;;
            esac ;;
        nginx)
            sudo_or_exit
            case $2 in
                install) install_nginx_site ;;
                remove) remove_nginx_site ;;
                *) usage "$_usage"; exit 42;;
            esac ;;
        option)
            sudo_or_exit
            case $2 in
                debug-on)  echo; enable_debug ;;
                debug-off)  echo; disable_debug ;;
                *) usage "$_usage"; exit 42;;
            esac ;;
        doc) rst-doc ;;
        *) usage "unknown or missing command $1"; exit 42;;
    esac
}

install_all() {
    rst_title "Install $SERVICE_NAME (service)"
    assert_user
    wait_key
    go.golang "${GO_VERSION}" "${SERVICE_USER}"
    wait_key
    install_filtron
    install_rules
    wait_key
    systemd_install_service "${SERVICE_NAME}" "${SERVICE_SYSTEMD_UNIT}"
    wait_key
    echo
    if ! service_is_available "http://${FILTRON_LISTEN}" ; then
        err_msg "Filtron is not listening on: http://${FILTRON_LISTEN}"
    fi
    if apache_is_installed; then
        info_msg "Apache is installed on this host."
        if ask_yn "Do you want to install a reverse proxy (ProxyPass)" Yn; then
            install_apache_site
        fi
    elif nginx_is_installed; then
        info_msg "nginx is installed on this host."
        if ask_yn "Do you want to install a reverse proxy (ProxyPass)" Yn; then
            install_nginx_site
        fi
    fi
    if ask_yn "Do you want to inspect the installation?" Ny; then
        inspect_service
    fi

}

install_check() {

    if service_account_is_available "$SERVICE_USER"; then
        info_msg "service account $SERVICE_USER available."
    else
        err_msg "service account $SERVICE_USER not available!"
    fi
    if go_is_available "$SERVICE_USER"; then
        info_msg "~$SERVICE_USER: go is installed"
    else
        err_msg "~$SERVICE_USER: go is not installed"
    fi
    if filtron_is_installed; then
        info_msg "~$SERVICE_USER: filtron app is installed"
    else
        err_msg "~$SERVICE_USER: filtron app is not installed!"
    fi

    if ! service_is_available "http://${FILTRON_API}"; then
        err_msg "API not available at: http://${FILTRON_API}"
    fi

    if ! service_is_available "http://${FILTRON_LISTEN}" ; then
        err_msg "Filtron is not listening on: http://${FILTRON_LISTEN}"
    fi

    if service_is_available "http://${FILTRON_TARGET}" ; then
        info_msg "Filtron's target is available at: http://${FILTRON_TARGET}"
    fi

    if ! service_is_available "${PUBLIC_URL}"; then
        warn_msg "Public service at ${PUBLIC_URL} is not available!"
        if ! in_container; then
            warn_msg "Check if public name is correct and routed or use the public IP from above."
        fi
    fi

    if [[ "${GO_VERSION}" > "$(go_version)" ]]; then
        warn_msg "golang ($(go_version)) needs to be $GO_VERSION at least"
        warn_msg "you need to reinstall $SERVICE_USER --> $0 reinstall all"
    else
        info_msg "golang $(go_version) is installed (min needed is: $GO_VERSION)"
    fi

    if [ -f "${APACHE_SITES_AVAILABLE}/searx.conf" ]; then
        warn_msg "old searx.conf apache site exists"
    fi

    if [ -f "${NGINX_APPS_AVAILABLE}/searx.conf" ]; then
        warn_msg "old searx.conf nginx site exists"
    fi

}

go_version(){
    go.version "${SERVICE_USER}"
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

assert_user() {
    rst_title "user $SERVICE_USER" section
    echo
    tee_stderr 1 <<EOF | bash | prefix_stdout
useradd --shell /bin/bash --system \
 --home-dir "$SERVICE_HOME" \
 --comment 'Reverse HTTP proxy to filter requests' $SERVICE_USER
mkdir "$SERVICE_HOME"
chown -R "$SERVICE_GROUP:$SERVICE_GROUP" "$SERVICE_HOME"
groups $SERVICE_USER
EOF
    SERVICE_HOME="$(sudo -i -u "$SERVICE_USER" echo \$HOME)"
    export SERVICE_HOME
    echo "export SERVICE_HOME=$SERVICE_HOME"

    tee_stderr <<EOF | sudo -i -u "$SERVICE_USER"
touch "$GO_ENV"
grep -qFs -- 'source "$GO_ENV"' ~/.profile || echo 'source "$GO_ENV"' >> ~/.profile
EOF
}

filtron_is_installed() {
    [[ -f $SERVICE_HOME/go-apps/bin/filtron ]]
}

install_filtron() {
    rst_title "Install filtron in user's ~/go-apps" section
    echo
    go.install github.com/searxng/filtron@latest "${SERVICE_USER}"
}

update_filtron() {
    rst_title "Update filtron" section
    echo
    go.install github.com/searxng/filtron@latest "${SERVICE_USER}"
}

install_rules() {
    rst_title "Install filtron rules"
    echo
    if [[ ! -f "${FILTRON_RULES}" ]]; then
        info_msg "install rules ${FILTRON_RULES_TEMPLATE}"
        info_msg "  --> ${FILTRON_RULES}"
        mkdir -p "$(dirname "${FILTRON_RULES}")"
        cp "${FILTRON_RULES_TEMPLATE}" "${FILTRON_RULES}"
        return
    fi

    if cmp --silent "${FILTRON_RULES}" "${FILTRON_RULES_TEMPLATE}"; then
        info_msg "${FILTRON_RULES} is up to date with"
        info_msg "${FILTRON_RULES_TEMPLATE}"
        return
    fi

    rst_para "Diff between origin's rules file (+) and current (-):"
    echo "${FILTRON_RULES}" "${FILTRON_RULES_TEMPLATE}"
    $DIFF_CMD "${FILTRON_RULES}" "${FILTRON_RULES_TEMPLATE}"

    local action
    choose_one action "What should happen to the rules file? " \
           "keep configuration unchanged" \
           "use origin rules" \
           "start interactive shell"
    case $action in
        "keep configuration unchanged")
            info_msg "leave rules file unchanged"
            ;;
        "use origin rules")
            backup_file "${FILTRON_RULES}"
            info_msg "install origin rules"
            cp "${FILTRON_RULES_TEMPLATE}" "${FILTRON_RULES}"
            ;;
        "start interactive shell")
            backup_file "${FILTRON_RULES}"
            echo -e "// exit with [${_BCyan}CTRL-D${_creset}]"
            sudo -H -i
            rst_para 'Diff between new rules file (-) and current (+):'
            echo
            $DIFF_CMD "${FILTRON_RULES_TEMPLATE}" "${FILTRON_RULES}"
            wait_key
            ;;
    esac
}

inspect_service() {

    rst_title "service status & log"

    cat <<EOF

sourced ${DOT_CONFIG} :
  SERVICE_USER        : ${SERVICE_USER}
  SERVICE_HOME        : ${SERVICE_HOME}
  FILTRON_TARGET      : ${FILTRON_TARGET}
  FILTRON_API         : ${FILTRON_API}
  FILTRON_LISTEN      : ${FILTRON_LISTEN}
  FILTRON_URL_PATH    : ${FILTRON_URL_PATH}
EOF
    install_log_searx_instance

    install_check

    if in_container; then
        lxc_suite_info
    else
        info_msg "public URL   --> ${PUBLIC_URL}"
        info_msg "internal URL --> http://${FILTRON_LISTEN}"
    fi


    local _debug_on
    if ask_yn "Enable filtron debug mode?"; then
        enable_debug
        _debug_on=1
    fi
    echo
    systemctl --no-pager -l status "${SERVICE_NAME}"
    echo

    info_msg "public URL --> ${PUBLIC_URL}"
    # shellcheck disable=SC2059
    printf "// use ${_BCyan}CTRL-C${_creset} to stop monitoring the log"
    read -r -s -n1 -t 5
    echo
    while true;  do
        trap break 2
        journalctl -f -u "${SERVICE_NAME}"
    done

    if [[ $_debug_on == 1 ]]; then
        disable_debug
    fi
    return 0
}


enable_debug() {
    info_msg "try to enable debug mode ..."
    python <<EOF
import sys, json

debug = {
    u'name': u'debug request'
    , u'filters': []
    , u'interval': 0
    , u'limit': 0
    , u'actions': [{u'name': u'log'}]
}

with open('$FILTRON_RULES') as rules:
    j = json.load(rules)

pos = None
for i in range(len(j)):
    if j[i].get('name') == 'debug request':
        pos = i
        break
if pos is not None:
    j[pos] = debug
else:
    j.append(debug)
with open('$FILTRON_RULES', 'w') as rules:
    json.dump(j, rules, indent=2, sort_keys=True)

EOF
    systemctl restart "${SERVICE_NAME}.service"
}

disable_debug() {
    info_msg "try to disable debug mode ..."
    python <<EOF
import sys, json
with open('$FILTRON_RULES') as rules:
    j = json.load(rules)

pos = None
for i in range(len(j)):
    if j[i].get('name') == 'debug request':
        pos = i
        break
if pos is not None:
    del j[pos]
    with open('$FILTRON_RULES', 'w') as rules:
         json.dump(j, rules, indent=2, sort_keys=True)
EOF
    systemctl restart "${SERVICE_NAME}.service"
}

install_apache_site() {

    rst_title "Install Apache site $APACHE_FILTRON_SITE"

    rst_para "\
This installs a reverse proxy (ProxyPass) into apache site (${APACHE_FILTRON_SITE})"

    ! apache_is_installed && info_msg "Apache is not installed."

    if ! ask_yn "Do you really want to continue?" Yn; then
        return
    else
        install_apache
    fi

    "${REPO_ROOT}/utils/searx.sh" install uwsgi

    apache_install_site --variant=filtron "${APACHE_FILTRON_SITE}"

    info_msg "testing public url .."
    if ! service_is_available "${PUBLIC_URL}"; then
        err_msg "Public service at ${PUBLIC_URL} is not available!"
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

install_nginx_site() {

    rst_title "Install nginx site $NGINX_FILTRON_SITE"

    rst_para "\
This installs a reverse proxy (ProxyPass) into nginx site (${NGINX_FILTRON_SITE})"

    ! nginx_is_installed && info_msg "nginx is not installed."

    if ! ask_yn "Do you really want to continue?" Yn; then
        return
    else
        install_nginx
    fi

    "${REPO_ROOT}/utils/searx.sh" install uwsgi

    # shellcheck disable=SC2034
    SEARX_SRC=$("${REPO_ROOT}/utils/searx.sh" --getenv SEARX_SRC)
    # shellcheck disable=SC2034
    SEARXNG_URL_PATH=$("${REPO_ROOT}/utils/searx.sh" --getenv SEARXNG_URL_PATH)
    nginx_install_app --variant=filtron "${NGINX_FILTRON_SITE}"

    info_msg "testing public url .."
    if ! service_is_available "${PUBLIC_URL}"; then
        err_msg "Public service at ${PUBLIC_URL} is not available!"
    fi
}

remove_nginx_site() {

    rst_title "Remove nginx site $NGINX_FILTRON_SITE"

    rst_para "\
This removes nginx site ${NGINX_FILTRON_SITE}."

    ! nginx_is_installed && err_msg "nginx is not installed."

    if ! ask_yn "Do you really want to continue?" Yn; then
        return
    fi

    nginx_remove_site "$FILTRON_FILTRON_SITE"

}


rst-doc() {

    eval "echo \"$(< "${REPO_ROOT}/docs/build-templates/filtron.rst")\""

    echo -e "\n.. START install systemd unit"
    cat <<EOF
.. tabs::

   .. group-tab:: systemd

      .. code:: bash

EOF
    eval "echo \"$(< "${TEMPLATES}/${SERVICE_SYSTEMD_UNIT}")\"" | prefix_stdout "         "
    echo -e "\n.. END install systemd unit"

    # for DIST_NAME in ubuntu-20.04 arch fedora centos; do
    #     (
    #         DIST_ID=${DIST_NAME%-*}
    #         DIST_VERS=${DIST_NAME#*-}
    #         [[ $DIST_VERS =~ $DIST_ID ]] && DIST_VERS=
    #         # ...
    #     )
    # done
}

# ----------------------------------------------------------------------------
main "$@"
# ----------------------------------------------------------------------------
