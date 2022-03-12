#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# shellcheck disable=SC2001

# shellcheck source=utils/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

# shellcheck source=utils/lib_install.sh
source "${REPO_ROOT}/utils/lib_install.sh"

# ----------------------------------------------------------------------------
# config
# ----------------------------------------------------------------------------

SEARX_INTERNAL_HTTP="${SEARXNG_BIND_ADDRESS}:${SEARXNG_PORT}"

SEARXNG_URL_PATH="${SEARXNG_URL_PATH:-$(echo "${PUBLIC_URL}" \
| sed -e 's,^.*://[^/]*\(/.*\),\1,g')}"
[[ "${SEARXNG_URL_PATH}" == "${PUBLIC_URL}" ]] && SEARXNG_URL_PATH=/

SERVICE_NAME="searx"
SERVICE_USER="${SERVICE_USER:-${SERVICE_NAME}}"
SERVICE_HOME_BASE="${SERVICE_HOME_BASE:-/usr/local}"
SERVICE_HOME="${SERVICE_HOME_BASE}/${SERVICE_USER}"
# shellcheck disable=SC2034
SERVICE_GROUP="${SERVICE_USER}"

GIT_BRANCH="${GIT_BRANCH:-master}"
SEARX_PYENV="${SERVICE_HOME}/searx-pyenv"
SEARX_SRC="${SERVICE_HOME}/searx-src"
SEARXNG_SETTINGS_PATH="/etc/searxng/settings.yml"
SEARXNG_UWSGI_APP="searxng.ini"
# shellcheck disable=SC2034
SEARX_UWSGI_SOCKET="/run/uwsgi/app/searxng/socket"

# apt packages
SEARX_PACKAGES_debian="\
python3-dev python3-babel python3-venv
uwsgi uwsgi-plugin-python3
git build-essential libxslt-dev zlib1g-dev libffi-dev libssl-dev
shellcheck"

BUILD_PACKAGES_debian="\
firefox graphviz imagemagick texlive-xetex librsvg2-bin
texlive-latex-recommended texlive-extra-utils fonts-dejavu
latexmk"

# pacman packages
SEARX_PACKAGES_arch="\
python python-pip python-lxml python-babel
uwsgi uwsgi-plugin-python
git base-devel libxml2
shellcheck"

BUILD_PACKAGES_arch="\
firefox graphviz imagemagick texlive-bin extra/librsvg
texlive-core texlive-latexextra ttf-dejavu"

# dnf packages
SEARX_PACKAGES_fedora="\
python python-pip python-lxml python-babel python3-devel
uwsgi uwsgi-plugin-python3
git @development-tools libxml2 openssl
ShellCheck"

BUILD_PACKAGES_fedora="\
firefox graphviz graphviz-gd ImageMagick librsvg2-tools
texlive-xetex-bin texlive-collection-fontsrecommended
texlive-collection-latex dejavu-sans-fonts dejavu-serif-fonts
dejavu-sans-mono-fonts"

# yum packages
#
# hint: We do no longer support yum packages, it is to complex to maintain
#       automate installation of packages like npm.  In the firts step we ignore
#       CentOS-7 as developer & build platform (the inital patch which brought
#       CentOS-7 supports was not intended to be a developer platform).

SEARX_PACKAGES_centos="\
python36 python36-pip python36-lxml python-babel
uwsgi uwsgi-plugin-python3
git @development-tools libxml2
ShellCheck"

BUILD_PACKAGES_centos="\
firefox graphviz graphviz-gd ImageMagick librsvg2-tools
texlive-xetex-bin texlive-collection-fontsrecommended
texlive-collection-latex dejavu-sans-fonts dejavu-serif-fonts
dejavu-sans-mono-fonts"

case $DIST_ID-$DIST_VERS in
    ubuntu-16.04|ubuntu-18.04)
        SEARX_PACKAGES="${SEARX_PACKAGES_debian}"
        BUILD_PACKAGES="${BUILD_PACKAGES_debian}"
        APACHE_PACKAGES="$APACHE_PACKAGES libapache2-mod-proxy-uwsgi"
        ;;
    ubuntu-20.04)
        # https://askubuntu.com/a/1224710
        SEARX_PACKAGES="${SEARX_PACKAGES_debian} python-is-python3"
        BUILD_PACKAGES="${BUILD_PACKAGES_debian}"
        ;;
    ubuntu-*|debian-*)
        SEARX_PACKAGES="${SEARX_PACKAGES_debian}"
        BUILD_PACKAGES="${BUILD_PACKAGES_debian}"
        ;;
    arch-*)
        SEARX_PACKAGES="${SEARX_PACKAGES_arch}"
        BUILD_PACKAGES="${BUILD_PACKAGES_arch}"
        ;;
    fedora-*)
        SEARX_PACKAGES="${SEARX_PACKAGES_fedora}"
        BUILD_PACKAGES="${BUILD_PACKAGES_fedora}"
        ;;
    centos-7)
        SEARX_PACKAGES="${SEARX_PACKAGES_centos}"
        BUILD_PACKAGES="${BUILD_PACKAGES_centos}"
        ;;
esac

# Apache Settings
APACHE_SEARX_SITE="searxng.conf"

# shellcheck disable=SC2034
CONFIG_FILES=(
    "${uWSGI_APPS_AVAILABLE}/${SEARXNG_UWSGI_APP}"
)

# shellcheck disable=SC2034
CONFIG_BACKUP_ENCRYPTED=(
    "${SEARXNG_SETTINGS_PATH}"
)

# ----------------------------------------------------------------------------
usage() {
# ----------------------------------------------------------------------------

    # shellcheck disable=SC1117
    cat <<EOF
usage::
  $(basename "$0") shell
  $(basename "$0") install    [all|check|init-src|dot-config|user|searx-src|pyenv|uwsgi|packages|settings|buildhost]
  $(basename "$0") reinstall  all
  $(basename "$0") update     [searx]
  $(basename "$0") remove     [all|user|pyenv|searx-src]
  $(basename "$0") activate   [service]
  $(basename "$0") deactivate [service]
  $(basename "$0") inspect    [service|settings <key>]
  $(basename "$0") option     [debug-[on|off]|image-proxy-[on|off]|result-proxy <url> <key>]
  $(basename "$0") apache     [install|remove]

shell
  start interactive shell from user ${SERVICE_USER}
install / remove
  :all:        complete (de-) installation of SearXNG service
  :user:       add/remove service user '$SERVICE_USER' ($SERVICE_HOME)
  :dot-config: copy ./config.sh to ${SEARX_SRC}
  :searx-src:  clone $GIT_URL
  :init-src:   copy files (SEARX_SRC_INIT_FILES) to ${SEARX_SRC}
  :pyenv:      create/remove virtualenv (python) in $SEARX_PYENV
  :uwsgi:      install SearXNG uWSGI application
  :settings:   reinstall settings from ${SEARXNG_SETTINGS_PATH}
  :packages:   install needed packages from OS package manager
  :buildhost:  install packages from OS package manager needed by buildhosts
install
  :check:      check the SearXNG installation
reinstall:
  :all:        runs 'install/remove all'
update searx
  Update SearXNG installation ($SERVICE_HOME)
activate service
  activate and start service daemon (systemd unit)
deactivate service
  stop and deactivate service daemon (systemd unit)
inspect
  :service:    run some small tests and inspect service's status and log
  :settings:   inspect YAML setting <key> from SearXNG instance (${SEARX_SRC})
option
  set one of the available options
apache
  :install: apache site with the SearXNG uwsgi app
  :remove:  apache site ${APACHE_FILTRON_SITE}
---- sourced ${DOT_CONFIG}
  SERVICE_USER        : ${SERVICE_USER}
  SERVICE_HOME        : ${SERVICE_HOME}
EOF

    install_log_searx_instance
    [[ -n ${1} ]] &&  err_msg "$1"
}

main() {
    required_commands \
        sudo systemctl install git wget curl \
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
                settings)
                    prompt_installation_setting "$3"
                    dump_return $?
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
            sudo_or_exit
            case $2 in
                all)
                    rst_title "SearXNG (install)" part
                    install_all
                    ;;
                check)
                    rst_title "SearXNG (check installation)" part
                    verify_continue_install
                    install_check
                    ;;
                user)
                    rst_title "SearXNG (install user)"
                    verify_continue_install
                    assert_user
                    ;;
                pyenv)
                    rst_title "SearXNG (install pyenv)"
                    verify_continue_install
                    create_pyenv
                    ;;
                searx-src)
                    rst_title "SearXNG (install searx-src)"
                    verify_continue_install
                    assert_user
                    clone_searx
                    install_DOT_CONFIG
                    init_SEARX_SRC
                    ;;
                init-src)
                    init_SEARX_SRC
                    ;;
                dot-config)
                    install_DOT_CONFIG
                    ;;
                settings)
                    install_settings
                    ;;
                uwsgi)
                    rst_title "SearXNG (install uwsgi)"
                    verify_continue_install
                    install_searx_uwsgi
                    if ! service_is_available "http://${SEARX_INTERNAL_HTTP}"; then
                        err_msg "URL http://${SEARX_INTERNAL_HTTP} not available, check SearXNG & uwsgi setup!"
                    fi
                    ;;
                packages)
                    rst_title "SearXNG (install packages)"
                    pkg_install "$SEARX_PACKAGES"
                    ;;
                buildhost)
                    rst_title "SearXNG (install buildhost)"
                    pkg_install "$SEARX_PACKAGES"
                    pkg_install "$BUILD_PACKAGES"
                    ;;
                *) usage "$_usage"; exit 42;;
            esac ;;
        update)
            sudo_or_exit
            case $2 in
                searx) update_searx;;
                *) usage "$_usage"; exit 42;;
            esac ;;
        remove)
            rst_title "SearXNG (remove)" part
            sudo_or_exit
            case $2 in
                all) remove_all;;
                user) drop_service_account "${SERVICE_USER}";;
                pyenv) remove_pyenv ;;
                searx-src) remove_searx ;;
                *) usage "$_usage"; exit 42;;
            esac ;;
        activate)
            sudo_or_exit
            case $2 in
                service)
                    activate_service ;;
                *) usage "$_usage"; exit 42;;
            esac ;;
        deactivate)
            sudo_or_exit
            case $2 in
                service)  deactivate_service ;;
                *) usage "$_usage"; exit 42;;
            esac ;;
        option)
            sudo_or_exit
            case $2 in
                debug-on)  echo; enable_debug ;;
                debug-off)  echo; disable_debug ;;
                result-proxy) set_result_proxy "$3" "$4" ;;
                image-proxy-on) enable_image_proxy ;;
                image-proxy-off) disable_image_proxy ;;
                *) usage "$_usage"; exit 42;;
            esac ;;
        apache)
            sudo_or_exit
            case $2 in
                install) install_apache_site ;;
                remove) remove_apache_site ;;
                *) usage "$_usage"; exit 42;;
            esac ;;
        doc) rst-doc;;
        *) usage "unknown or missing command $1"; exit 42;;
    esac
}

_service_prefix="  ${_Yellow}|$SERVICE_USER|${_creset} "

install_all() {
    rst_title "Install SearXNG (service)"
    verify_continue_install
    pkg_install "$SEARX_PACKAGES"
    wait_key
    assert_user
    wait_key
    clone_searx
    wait_key
    install_DOT_CONFIG
    wait_key
    init_SEARX_SRC
    wait_key
    create_pyenv
    wait_key
    install_settings
    wait_key
    test_local_searx
    wait_key
    install_searx_uwsgi
    if ! service_is_available "http://${SEARX_INTERNAL_HTTP}"; then
        err_msg "URL http://${SEARX_INTERNAL_HTTP} not available, check SearXNG & uwsgi setup!"
    fi
    if ask_yn "Do you want to inspect the installation?" Ny; then
        inspect_service
    fi
}

install_check() {
    if service_account_is_available "$SERVICE_USER"; then
        info_msg "Service account $SERVICE_USER exists."
    else
        err_msg "Service account $SERVICE_USER does not exists!"
    fi

    if pyenv_is_available; then
        info_msg "~$SERVICE_USER: python environment is available."
    else
        err_msg "~$SERVICE_USER: python environment is not available!"
    fi

    if clone_is_available; then
        info_msg "~$SERVICE_USER: SearXNG software is installed."
    else
        err_msg "~$SERVICE_USER: Missing SearXNG software!"
    fi

    if uWSGI_app_enabled "$SEARXNG_UWSGI_APP"; then
        info_msg "uWSGI app $SEARXNG_UWSGI_APP is enabled."
    else
        err_msg "uWSGI app $SEARXNG_UWSGI_APP not enabled!"
    fi

    uWSGI_app_available "$SEARXNG_UWSGI_APP" \
        || err_msg "uWSGI app $SEARXNG_UWSGI_APP not available!"

    sudo -H -u "${SERVICE_USER}" "${SEARX_PYENV}/bin/python" "utils/searxng_check.py"

    if uWSGI_app_available 'searx.ini'; then
        warn_msg "old searx.ini uWSGI app exists"
        warn_msg "you need to reinstall $SERVICE_USER --> $0 reinstall all"
    fi
}

update_searx() {
    rst_title "Update SearXNG instance"

    rst_para "fetch from $GIT_URL and reset to origin/$GIT_BRANCH"
    tee_stderr 0.3 <<EOF | sudo -H -u "${SERVICE_USER}" -i 2>&1 |  prefix_stdout "$_service_prefix"
cd ${SEARX_SRC}
git fetch origin "$GIT_BRANCH"
git reset --hard "origin/$GIT_BRANCH"
pip install -U pip
pip install -U setuptools
pip install -U wheel
pip install -U pyyaml
pip install -U -e .
EOF
    install_settings
    uWSGI_restart "$SEARXNG_UWSGI_APP"
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

assert_user() {
    rst_title "user $SERVICE_USER" section
    echo
    if getent passwd "$SERVICE_USER"  > /dev/null; then
       echo "user exists"
       return 0
    fi

    tee_stderr 1 <<EOF | bash | prefix_stdout
useradd --shell /bin/bash --system \
 --home-dir "$SERVICE_HOME" \
 --comment 'Privacy-respecting metasearch engine' $SERVICE_USER
mkdir "$SERVICE_HOME"
chown -R "$SERVICE_GROUP:$SERVICE_GROUP" "$SERVICE_HOME"
groups $SERVICE_USER
EOF
    #SERVICE_HOME="$(sudo -i -u "$SERVICE_USER" echo \$HOME)"
    #export SERVICE_HOME
    #echo "export SERVICE_HOME=$SERVICE_HOME"
}

clone_is_available() {
    [[ -f "$SEARX_SRC/.git/config" ]]
}

# shellcheck disable=SC2164
clone_searx() {
    rst_title "Clone SearXNG sources" section
    echo
    if ! sudo -i -u "$SERVICE_USER" ls -d "$REPO_ROOT" > /dev/null; then
        die 42 "user '$SERVICE_USER' missed read permission: $REPO_ROOT"
    fi
    SERVICE_HOME="$(sudo -i -u "$SERVICE_USER" echo \$HOME 2>/dev/null)"
    if [[ ! "${SERVICE_HOME}" ]]; then
        err_msg "to clone SearXNG sources, user $SERVICE_USER hast to be created first"
        return 42
    fi
    if [[ ! $(git show-ref "refs/heads/${GIT_BRANCH}") ]]; then
        warn_msg "missing local branch ${GIT_BRANCH}"
        info_msg "create local branch ${GIT_BRANCH} from start point: origin/${GIT_BRANCH}"
        git branch "${GIT_BRANCH}" "origin/${GIT_BRANCH}"
    fi
    if [[ ! $(git rev-parse --abbrev-ref HEAD) == "${GIT_BRANCH}" ]]; then
        warn_msg "take into account, installing branch $GIT_BRANCH while current branch is $(git rev-parse --abbrev-ref HEAD)"
    fi
    export SERVICE_HOME
    git_clone "$REPO_ROOT" "$SEARX_SRC" \
              "$GIT_BRANCH" "$SERVICE_USER"

    pushd "${SEARX_SRC}" > /dev/null
    tee_stderr 0.1 <<EOF | sudo -H -u "${SERVICE_USER}" -i 2>&1 | prefix_stdout "$_service_prefix"
cd "${SEARX_SRC}"
git remote set-url origin ${GIT_URL}
git config user.email "$ADMIN_EMAIL"
git config user.name "$ADMIN_NAME"
git config --list
EOF
    popd > /dev/null
}

prompt_installation_status(){

    # shellcheck disable=SC2034
    local GIT_URL GIT_BRANCH VERSION_STRING VERSION_TAG
    local ret_val state branch remote remote_url
    state="$(install_searx_get_state)"

    case $state in
        missing-searx-clone|missing-searx-pyenv)
            info_msg "${_BBlue}(status: $(install_searx_get_state))${_creset}"
            return 0
            ;;
        *)
            info_msg "SearXNG instance already installed at: $SEARX_SRC"
            info_msg "status:  ${_BBlue}$(install_searx_get_state)${_creset} "
            branch="$(git name-rev --name-only HEAD)"
            remote="$(git config branch."${branch}".remote)"
            remote_url="$(git config remote."${remote}".url)"
            eval "$(get_installed_version_variables)"

            ret_val=0
            if ! [ "$GIT_URL" = "$remote_url" ]; then
                warn_msg "instance's git URL: '${GIT_URL}'" \
                         "differs from local clone's remote URL: ${remote_url}"
                ret_val=42
            fi
            if ! [ "$GIT_BRANCH" = "$branch" ]; then
                warn_msg "instance git branch: ${GIT_BRANCH}" \
                         "differs from local clone's branch: ${branch}"
                ret_val=42
            fi
            return $ret_val
            ;;
    esac
}

verify_continue_install(){
    if ! prompt_installation_status; then
        MSG="[${_BCyan}KEY${_creset}] to continue installation / [${_BCyan}CTRL-C${_creset}] to exit" \
           wait_key
    fi
}

prompt_installation_setting(){

    # usage:  prompt_installation_setting brand.docs_url
    #
    # Prompts the value of the (YAML) setting in the SearXNG instance.

    local _state
    _state="$(install_searx_get_state)"
    case $_state in
        python-installed|installer-modified)
            sudo -H -u "${SERVICE_USER}" "${SEARX_PYENV}/bin/python" <<EOF
import sys
from searx import get_setting
name = "${1}"
unset = object()
value = get_setting(name, unset)
if value is unset:
    sys.stderr.write("error: setting '%s' does not exists\n" % name)
    sys.exit(42)
print(value)
sys.exit(0)
EOF
            ;;
        *)
            return 42
            ;;
    esac
}

get_installed_version_variables() {

    # usage:  eval "$(get_installed_version_variables)"
    #
    # Set variables VERSION_STRING, VERSION_TAG, GIT_URL, GIT_BRANCH

    local _state
    _state="$(install_searx_get_state)"
    case $_state in
        python-installed|installer-modified)
            sudo -H -u "${SERVICE_USER}" "${SEARX_PYENV}/bin/python" -m searx.version;;
        *)
            return 42
            ;;
    esac
}

init_SEARX_SRC(){
    rst_title "Update instance: ${SEARX_SRC}/" section

    if ! clone_is_available; then
        err_msg "you have to install SearXNG first"
        return 1
    fi

    init_SEARX_SRC_INIT_FILES

    if [ ${#SEARX_SRC_INIT_FILES[*]} -eq 0 ]; then
        info_msg "no files registered in SEARX_SRC_INIT_FILES"
        return 2
    fi

    echo
    echo "Update instance with file(s) from: ${REPO_ROOT}"
    echo
    for i in "${SEARX_SRC_INIT_FILES[@]}"; do
        echo "- $i"
    done
    echo
    echo "Be careful when modifying an existing installation."
    if ! ask_yn "Do you really want to update these files in the instance?" Yn; then
        return 42
    fi
    for fname in "${SEARX_SRC_INIT_FILES[@]}"; do
        while true; do
            choose_one _reply "choose next step with file ${fname}" \
                   "replace file" \
                   "leave file unchanged" \
                   "diff files" \
                   "interactive shell"

            case $_reply in
                "leave file unchanged")
                    break
                    ;;
                "replace file")
                    info_msg "copy: ${REPO_ROOT}/${fname} --> ${SEARX_SRC}/${fname}"
                    cp "${REPO_ROOT}/${fname}" "${SEARX_SRC}/${fname}"
                    break
                    ;;
                "diff files")
                    $DIFF_CMD "${SEARX_SRC}/${fname}" "${REPO_ROOT}/${fname}"
                    ;;
                "interactive shell")
                    backup_file "${SEARX_SRC}/${fname}"
                    echo -e "// edit ${_Red}${dst}${_creset} to your needs"
                    echo -e "// exit with [${_BCyan}CTRL-D${_creset}]"
                    sudo -H -u "${SERVICE_USER}" -i
                    $DIFF_CMD "${SEARX_SRC}/${fname}"  "${REPO_ROOT}/${fname}"
                    echo
                    echo -e "// ${_BBlack}did you edit file ...${_creset}"
                    echo -en "//  ${_Red}${dst}${_creset}"
                    if ask_yn "//${_BBlack}... to your needs?${_creset}"; then
                        break
                    fi
                    ;;
            esac
        done
    done
}

install_DOT_CONFIG(){
    rst_title "Update instance: ${SEARX_SRC}/.config.sh" section

    if cmp --silent "${REPO_ROOT}/.config.sh" "${SEARX_SRC}/.config.sh"; then
        info_msg "${SEARX_SRC}/.config.sh is up to date"
        return 0
    fi

    diff "${REPO_ROOT}/.config.sh" "${SEARX_SRC}/.config.sh"
    if ! ask_yn "Do you want to copy file .config.sh into instance?" Yn; then
        return 42
    fi
    backup_file "${SEARX_SRC}/.config.sh"
    cp "${REPO_ROOT}/.config.sh" "${SEARX_SRC}/.config.sh"
}

install_settings() {
    rst_title "${SEARXNG_SETTINGS_PATH}" section

    if ! clone_is_available; then
        err_msg "you have to install SearXNG first"
        exit 42
    fi

    mkdir -p "$(dirname "${SEARXNG_SETTINGS_PATH}")"
    install_template --no-eval \
        "${SEARXNG_SETTINGS_PATH}" \
        "${SERVICE_USER}" "${SERVICE_GROUP}"
    configure_searx
}

remove_settings() {
    rst_title "remove SearXNG settings" section
    echo
    info_msg "delete ${SEARXNG_SETTINGS_PATH}"
    rm -f "${SEARXNG_SETTINGS_PATH}"
}

remove_searx() {
    rst_title "Drop SearXNG sources" section
    if ask_yn "Do you really want to drop SearXNG sources ($SEARX_SRC)?"; then
        rm -rf "$SEARX_SRC"
    else
        rst_para "Leave SearXNG sources unchanged."
    fi
}

pyenv_is_available() {
    [[ -f "${SEARX_PYENV}/bin/activate" ]]
}

create_pyenv() {
    rst_title "Create virtualenv (python)" section
    echo
    if [[ ! -f "${SEARX_SRC}/manage" ]]; then
        err_msg "to create pyenv for SearXNG, SearXNG has to be cloned first"
        return 42
    fi
    info_msg "create pyenv in ${SEARX_PYENV}"
    tee_stderr 0.1 <<EOF | sudo -H -u "${SERVICE_USER}" -i 2>&1 |  prefix_stdout "$_service_prefix"
rm -rf "${SEARX_PYENV}"
python3 -m venv "${SEARX_PYENV}"
grep -qFs -- 'source ${SEARX_PYENV}/bin/activate' ~/.profile \
  || echo 'source ${SEARX_PYENV}/bin/activate' >> ~/.profile
EOF
    info_msg "inspect python's virtual environment"
    tee_stderr 0.1 <<EOF | sudo -H -u "${SERVICE_USER}" -i 2>&1 |  prefix_stdout "$_service_prefix"
command -v python && python --version
EOF
    wait_key
    info_msg "install needed python packages"
    tee_stderr 0.1 <<EOF | sudo -H -u "${SERVICE_USER}" -i 2>&1 |  prefix_stdout "$_service_prefix"
pip install -U pip
pip install -U setuptools
pip install -U wheel
pip install -U pyyaml
cd ${SEARX_SRC}
pip install -e .
EOF
}

remove_pyenv() {
    rst_title "Remove virtualenv (python)" section
    if ! ask_yn "Do you really want to drop ${SEARX_PYENV} ?"; then
        return
    fi
    info_msg "remove pyenv activation from ~/.profile"
    tee_stderr 0.1 <<EOF | sudo -H -u "${SERVICE_USER}" -i 2>&1 |  prefix_stdout "$_service_prefix"
grep -v 'source ${SEARX_PYENV}/bin/activate' ~/.profile > ~/.profile.##
mv ~/.profile.## ~/.profile
EOF
    rm -rf "${SEARX_PYENV}"
}

configure_searx() {
    rst_title "Configure SearXNG" section
    rst_para "Setup SearXNG config located at $SEARXNG_SETTINGS_PATH"
    echo
    tee_stderr 0.1 <<EOF | sudo -H -i 2>&1 |  prefix_stdout "$_service_prefix"
cd ${SEARX_SRC}
sed -i -e "s/ultrasecretkey/$(openssl rand -hex 16)/g" "$SEARXNG_SETTINGS_PATH"
EOF
}

test_local_searx() {
    rst_title "Testing SearXNG instance localy" section
    echo

    if service_is_available "http://${SEARX_INTERNAL_HTTP}" &>/dev/null; then
        err_msg "URL/port http://${SEARX_INTERNAL_HTTP} is already in use, you"
        err_msg "should stop that service before starting local tests!"
        if ! ask_yn "Continue with local tests?"; then
            return
        fi
    fi
    sed -i -e "s/debug: false/debug: true/g" "$SEARXNG_SETTINGS_PATH"
    tee_stderr 0.1 <<EOF | sudo -H -u "${SERVICE_USER}" -i 2>&1 |  prefix_stdout "$_service_prefix"
export SEARXNG_SETTINGS_PATH="${SEARXNG_SETTINGS_PATH}"
cd ${SEARX_SRC}
timeout 10 python searx/webapp.py &
sleep 3
curl --location --verbose --head --insecure $SEARX_INTERNAL_HTTP
EOF
    sed -i -e "s/debug: true/debug: false/g" "$SEARXNG_SETTINGS_PATH"
}

install_searx_uwsgi() {
    rst_title "Install SearXNG's uWSGI app (searxng.ini)" section
    echo
    install_uwsgi
    uWSGI_install_app "$SEARXNG_UWSGI_APP"
}

remove_searx_uwsgi() {
    rst_title "Remove SearXNG's uWSGI app (searxng.ini)" section
    echo
    uWSGI_remove_app "$SEARXNG_UWSGI_APP"
}

activate_service() {
    rst_title "Activate SearXNG (service)" section
    echo
    uWSGI_enable_app "$SEARXNG_UWSGI_APP"
    uWSGI_restart "$SEARXNG_UWSGI_APP"
}

deactivate_service() {
    rst_title "De-Activate SearXNG (service)" section
    echo
    uWSGI_disable_app "$SEARXNG_UWSGI_APP"
    uWSGI_restart "$SEARXNG_UWSGI_APP"
}

enable_image_proxy() {
    info_msg "try to enable image_proxy ..."
    tee_stderr 0.1 <<EOF | sudo -H -i 2>&1 |  prefix_stdout "$_service_prefix"
cd ${SEARX_SRC}
sed -i -e "s/image_proxy: false/image_proxy: true/g" "$SEARXNG_SETTINGS_PATH"
EOF
    uWSGI_restart "$SEARXNG_UWSGI_APP"
}

disable_image_proxy() {
    info_msg "try to enable image_proxy ..."
    tee_stderr 0.1 <<EOF | sudo -H -i 2>&1 |  prefix_stdout "$_service_prefix"
cd ${SEARX_SRC}
sed -i -e "s/image_proxy: true/image_proxy: false/g" "$SEARXNG_SETTINGS_PATH"
EOF
    uWSGI_restart "$SEARXNG_UWSGI_APP"
}

enable_debug() {
    warn_msg "Do not enable debug in production environments!!"
    info_msg "try to enable debug mode ..."
    tee_stderr 0.1 <<EOF | sudo -H -i 2>&1 |  prefix_stdout "$_service_prefix"
cd ${SEARX_SRC}
sed -i -e "s/debug: false/debug: true/g" "$SEARXNG_SETTINGS_PATH"
EOF
    uWSGI_restart "$SEARXNG_UWSGI_APP"
}

disable_debug() {
    info_msg "try to disable debug mode ..."
    tee_stderr 0.1 <<EOF | sudo -H -i 2>&1 |  prefix_stdout "$_service_prefix"
cd ${SEARX_SRC}
sed -i -e "s/debug: true/debug: false/g" "$SEARXNG_SETTINGS_PATH"
EOF
    uWSGI_restart "$SEARXNG_UWSGI_APP"
}

set_result_proxy() {

    # usage: set_result_proxy <URL> [<key>]

    info_msg "try to set result proxy: '$1' ($2)"
    cp "${SEARXNG_SETTINGS_PATH}" "${SEARXNG_SETTINGS_PATH}.bak"
    _set_result_proxy "$1" "$2" > "${SEARXNG_SETTINGS_PATH}"
}

_set_result_proxy() {
    local line
    local stage=0
    local url="    url: $1"
    local key="    key: !!binary \"$2\""
    if [[ -z $2 ]]; then
       key=
    fi

    while IFS=  read -r line
    do
        if [[ $stage = 0 ]] || [[ $stage = 2 ]] ; then
            if [[ $line =~ ^[[:space:]]*#*[[:space:]]*result_proxy[[:space:]]*:[[:space:]]*$ ]]; then
                if [[ $stage = 0 ]]; then
                    stage=1
                    echo "result_proxy:"
                    continue
                elif [[ $stage = 2 ]]; then
                    continue
                fi
            fi
        fi
        if [[ $stage = 1 ]] || [[ $stage = 2 ]] ; then
            if [[ $line =~ ^[[:space:]]*#*[[:space:]]*url[[:space:]]*:[[:space:]] ]]; then
                [[ $stage = 1 ]]  && echo "$url"
                continue
            elif [[ $line =~ ^[[:space:]]*#*[[:space:]]*key[[:space:]]*:[[:space:]] ]]; then
                [[ $stage = 1 ]] && [[ -n $key ]] && echo "$key"
                continue
            elif [[ $line =~ ^[[:space:]]*$ ]]; then
                stage=2
            fi
        fi
        echo "$line"
    done < "${SEARXNG_SETTINGS_PATH}.bak"
}

function has_substring() {
   [[ "$1" != "${2/$1/}" ]]
}
inspect_service() {
    rst_title "service status & log"
    cat <<EOF

sourced ${DOT_CONFIG} :
  SERVICE_USER        : ${SERVICE_USER}
  SERVICE_HOME        : ${SERVICE_HOME}
EOF
    install_log_searx_instance

    install_check
    if in_container; then
        lxc_suite_info
    else
        info_msg "public URL   --> ${PUBLIC_URL}"
        info_msg "internal URL --> http://${SEARX_INTERNAL_HTTP}"
    fi

    if ! service_is_available "http://${SEARX_INTERNAL_HTTP}"; then
        err_msg "uWSGI app (service) at http://${SEARX_INTERNAL_HTTP} is not available!"
        MSG="${_Green}[${_BCyan}CTRL-C${_Green}] to stop or [${_BCyan}KEY${_Green}] to continue"\
           wait_key
    fi

    if ! service_is_available "${PUBLIC_URL}"; then
        warn_msg "Public service at ${PUBLIC_URL} is not available!"
        if ! in_container; then
            warn_msg "Check if public name is correct and routed or use the public IP from above."
        fi
    fi

    local _debug_on
    if ask_yn "Enable SearXNG debug mode?"; then
        enable_debug
        _debug_on=1
    fi
    echo

    case $DIST_ID-$DIST_VERS in
        ubuntu-*|debian-*)
            systemctl --no-pager -l status "${SERVICE_NAME}"
            ;;
        arch-*)
            systemctl --no-pager -l status "uwsgi@${SERVICE_NAME%.*}"
            ;;
        fedora-*|centos-7)
            systemctl --no-pager -l status uwsgi
            ;;
    esac

    # shellcheck disable=SC2059
    printf "// use ${_BCyan}CTRL-C${_creset} to stop monitoring the log"
    read -r -s -n1 -t 5
    echo

    while true;  do
        trap break 2
        case $DIST_ID-$DIST_VERS in
            ubuntu-*|debian-*) tail -f /var/log/uwsgi/app/searx.log ;;
            arch-*)  journalctl -f -u "uwsgi@${SERVICE_NAME%.*}" ;;
            fedora-*|centos-7)  journalctl -f -u uwsgi ;;
        esac
    done

    if [[ $_debug_on == 1 ]]; then
        disable_debug
    fi
    return 0
}

install_apache_site() {
    rst_title "Install Apache site $APACHE_SEARX_SITE"

    rst_para "\
This installs the SearXNG uwsgi app as apache site.  If your server is public to
the internet, you should instead use a reverse proxy (filtron) to block
excessively bot queries."

    ! apache_is_installed && err_msg "Apache is not installed."

    if ! ask_yn "Do you really want to continue?" Yn; then
        return
    else
        install_apache
    fi

    apache_install_site --variant=uwsgi "${APACHE_SEARX_SITE}"

    rst_title "Install SearXNG's uWSGI app (searxng.ini)" section
    echo
    uWSGI_install_app --variant=socket "$SEARXNG_UWSGI_APP"

    if ! service_is_available "${PUBLIC_URL}"; then
        err_msg "Public service at ${PUBLIC_URL} is not available!"
    fi
}

remove_apache_site() {

    rst_title "Remove Apache site ${APACHE_SEARX_SITE}"

    rst_para "\
This removes apache site ${APACHE_SEARX_SITE}."

    ! apache_is_installed && err_msg "Apache is not installed."

    if ! ask_yn "Do you really want to continue?" Yn; then
        return
    fi

    apache_remove_site "${APACHE_SEARX_SITE}"

    rst_title "Remove SearXNG's uWSGI app (searxng.ini)" section
    echo
    uWSGI_remove_app "$SEARXNG_UWSGI_APP"
}

rst-doc() {
    local debian="${SEARX_PACKAGES_debian}"
    local arch="${SEARX_PACKAGES_arch}"
    local fedora="${SEARX_PACKAGES_fedora}"
    local centos="${SEARX_PACKAGES_centos}"
    local debian_build="${BUILD_PACKAGES_debian}"
    local arch_build="${BUILD_PACKAGES_arch}"
    local fedora_build="${BUILD_PACKAGES_fedora}"
    local centos_build="${SEARX_PACKAGES_centos}"
    debian="$(echo "${debian}" | sed 's/.*/          & \\/' | sed '$ s/.$//')"
    arch="$(echo "${arch}"     | sed 's/.*/          & \\/' | sed '$ s/.$//')"
    fedora="$(echo "${fedora}" | sed 's/.*/          & \\/' | sed '$ s/.$//')"
    centos="$(echo "${centos}" | sed 's/.*/          & \\/' | sed '$ s/.$//')"
    debian_build="$(echo "${debian_build}" | sed 's/.*/          & \\/' | sed '$ s/.$//')"
    arch_build="$(echo "${arch_build}"     | sed 's/.*/          & \\/' | sed '$ s/.$//')"
    fedora_build="$(echo "${fedora_build}" | sed 's/.*/          & \\/' | sed '$ s/.$//')"
    centos_build="$(echo "${centos_build}" | sed 's/.*/          & \\/' | sed '$ s/.$//')"

    eval "echo \"$(< "${REPO_ROOT}/docs/build-templates/searx.rst")\""

    # I use ubuntu-20.04 here to demonstrate that versions are also suported,
    # normaly debian-* and ubuntu-* are most the same.

    for DIST_NAME in ubuntu-20.04 arch fedora; do
        (
            DIST_ID=${DIST_NAME%-*}
            DIST_VERS=${DIST_NAME#*-}
            [[ $DIST_VERS =~ $DIST_ID ]] && DIST_VERS=
            uWSGI_distro_setup

            echo -e "\n.. START searxng uwsgi-description $DIST_NAME"

            case $DIST_ID-$DIST_VERS in
                ubuntu-*|debian-*)  cat <<EOF

.. code:: bash

   # init.d --> /usr/share/doc/uwsgi/README.Debian.gz
   # For uWSGI debian uses the LSB init process, this might be changed
   # one day, see https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=833067

   create     ${uWSGI_APPS_AVAILABLE}/${SEARXNG_UWSGI_APP}
   enable:    sudo -H ln -s ${uWSGI_APPS_AVAILABLE}/${SEARXNG_UWSGI_APP} ${uWSGI_APPS_ENABLED}/
   start:     sudo -H service uwsgi start   ${SEARXNG_UWSGI_APP%.*}
   restart:   sudo -H service uwsgi restart ${SEARXNG_UWSGI_APP%.*}
   stop:      sudo -H service uwsgi stop    ${SEARXNG_UWSGI_APP%.*}
   disable:   sudo -H rm ${uWSGI_APPS_ENABLED}/${SEARXNG_UWSGI_APP}

EOF
                ;;
                arch-*) cat <<EOF

.. code:: bash

   # systemd --> /usr/lib/systemd/system/uwsgi@.service
   # For uWSGI archlinux uses systemd template units, see
   # - http://0pointer.de/blog/projects/instances.html
   # - https://uwsgi-docs.readthedocs.io/en/latest/Systemd.html#one-service-per-app-in-systemd

   create:    ${uWSGI_APPS_ENABLED}/${SEARXNG_UWSGI_APP}
   enable:    sudo -H systemctl enable   uwsgi@${SEARXNG_UWSGI_APP%.*}
   start:     sudo -H systemctl start    uwsgi@${SEARXNG_UWSGI_APP%.*}
   restart:   sudo -H systemctl restart  uwsgi@${SEARXNG_UWSGI_APP%.*}
   stop:      sudo -H systemctl stop     uwsgi@${SEARXNG_UWSGI_APP%.*}
   disable:   sudo -H systemctl disable  uwsgi@${SEARXNG_UWSGI_APP%.*}

EOF
                ;;
                fedora-*|centos-7) cat <<EOF

.. code:: bash

   # systemd --> /usr/lib/systemd/system/uwsgi.service
   # The unit file starts uWSGI in emperor mode (/etc/uwsgi.ini), see
   # - https://uwsgi-docs.readthedocs.io/en/latest/Emperor.html

   create:    ${uWSGI_APPS_ENABLED}/${SEARXNG_UWSGI_APP}
   restart:   sudo -H touch ${uWSGI_APPS_ENABLED}/${SEARXNG_UWSGI_APP}
   disable:   sudo -H rm ${uWSGI_APPS_ENABLED}/${SEARXNG_UWSGI_APP}

EOF
                ;;
            esac
            echo -e ".. END searxng uwsgi-description $DIST_NAME"

            echo -e "\n.. START searxng uwsgi-appini $DIST_NAME"
            echo ".. code:: bash"
            echo
            eval "echo \"$(< "${TEMPLATES}/${uWSGI_APPS_AVAILABLE}/${SEARXNG_UWSGI_APP}")\"" | prefix_stdout "  "
            echo -e "\n.. END searxng uwsgi-appini $DIST_NAME"

        )
    done

}

# ----------------------------------------------------------------------------
main "$@"
# ----------------------------------------------------------------------------
