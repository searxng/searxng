#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# shellcheck disable=SC2001

# Script options from the environment:
ZHENSA_UWSGI_USE_SOCKET="${ZHENSA_UWSGI_USE_SOCKET:-true}"

# shellcheck source=utils/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
# shellcheck source=utils/lib_redis.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib_redis.sh"
# shellcheck source=utils/lib_valkey.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib_valkey.sh"
# shellcheck source=utils/brand.sh
source "${REPO_ROOT}/utils/brand.sh"

SERVICE_NAME="zhensa"
SERVICE_USER="zhensa"
SERVICE_HOME="/usr/local/zhensa"
SERVICE_GROUP="zhensa"

ZHENSA_SRC="${SERVICE_HOME}/zhensa-src"
# shellcheck disable=SC2034
ZHENSA_STATIC="${ZHENSA_SRC}/zhensa/static"

ZHENSA_PYENV="${SERVICE_HOME}/zhensa-pyenv"
ZHENSA_SETTINGS_PATH="/etc/zhensa/settings.yml"
ZHENSA_UWSGI_APP="zhensa.ini"

ZHENSA_INTERNAL_HTTP="${ZHENSA_BIND_ADDRESS}:${ZHENSA_PORT}"
if [[ ${ZHENSA_UWSGI_USE_SOCKET} == true ]]; then
    ZHENSA_UWSGI_SOCKET="${SERVICE_HOME}/run/socket"
else
    ZHENSA_UWSGI_SOCKET=
fi

# ZHENSA_URL: the public URL of the instance (https://example.org/zhensa).  The
# value is taken from environment ${ZHENSA_URL} in ./utils/brand.env.  This
# variable is an empty string if server.base_url in the settings.yml is set to
# 'false'.

ZHENSA_URL="${ZHENSA_URL:-http://$(uname -n)/zhensa}"
ZHENSA_URL="${ZHENSA_URL%/}" # if exists, remove trailing slash
ZHENSA_URL_PATH="$(echo "${ZHENSA_URL}" | sed -e 's,^.*://[^/]*\(/.*\),\1,g')"
[[ "${ZHENSA_URL_PATH}" == "${ZHENSA_URL}" ]] && ZHENSA_URL_PATH=/

# Apache settings

APACHE_ZHENSA_SITE="zhensa.conf"

# nginx settings

NGINX_ZHENSA_SITE="zhensa.conf"

# apt packages

ZHENSA_PACKAGES_debian="\
python3-dev python3-babel python3-venv python-is-python3
uwsgi uwsgi-plugin-python3
git build-essential libxslt-dev zlib1g-dev libffi-dev libssl-dev"

ZHENSA_BUILD_PACKAGES_debian="\
graphviz imagemagick texlive-xetex librsvg2-bin
texlive-latex-recommended texlive-extra-utils fonts-dejavu
latexmk shellcheck"

# pacman packages

ZHENSA_PACKAGES_arch="\
python python-pip python-lxml python-babel
uwsgi uwsgi-plugin-python
git base-devel libxml2"

ZHENSA_BUILD_PACKAGES_arch="\
graphviz imagemagick texlive-bin extra/librsvg
texlive-core texlive-latexextra ttf-dejavu shellcheck"

# dnf packages

ZHENSA_PACKAGES_fedora="\
python python-pip python-lxml python-babel python3-devel
uwsgi uwsgi-plugin-python3
git @development-tools libxml2 openssl"

ZHENSA_BUILD_PACKAGES_fedora="\
graphviz graphviz-gd ImageMagick librsvg2-tools
texlive-xetex-bin texlive-collection-fontsrecommended
texlive-collection-latex dejavu-sans-fonts dejavu-serif-fonts
dejavu-sans-mono-fonts ShellCheck"

case $DIST_ID-$DIST_VERS in
    ubuntu-18.04)
        ZHENSA_PACKAGES="${ZHENSA_PACKAGES_debian}"
        ZHENSA_BUILD_PACKAGES="${ZHENSA_BUILD_PACKAGES_debian}"
        APACHE_PACKAGES="$APACHE_PACKAGES libapache2-mod-proxy-uwsgi"
        ;;
    ubuntu-* | debian-*)
        ZHENSA_PACKAGES="${ZHENSA_PACKAGES_debian} python-is-python3"
        ZHENSA_BUILD_PACKAGES="${ZHENSA_BUILD_PACKAGES_debian}"
        ;;
    arch-*)
        ZHENSA_PACKAGES="${ZHENSA_PACKAGES_arch}"
        ZHENSA_BUILD_PACKAGES="${ZHENSA_BUILD_PACKAGES_arch}"
        ;;
    fedora-*)
        ZHENSA_PACKAGES="${ZHENSA_PACKAGES_fedora}"
        ZHENSA_BUILD_PACKAGES="${ZHENSA_BUILD_PACKAGES_fedora}"
        ;;
esac

_service_prefix="  ${_Yellow}|${SERVICE_USER}|${_creset} "

usage() {

    # shellcheck disable=SC1117
    cat <<EOF
usage:
  $(basename "$0") install    [all|user|pyenv|settings|uwsgi|valkey|nginx|apache|zhensa-src|packages|buildhost]
  $(basename "$0") remove     [all|user|pyenv|settings|uwsgi|valkey|nginx|apache]
  $(basename "$0") instance   [cmd|update|check|localtest|inspect]
install|remove:
  all           : complete (de-) installation of the Zhensa service
  user          : service user '${SERVICE_USER}' (${SERVICE_HOME})
  pyenv         : virtualenv (python) in ${ZHENSA_PYENV}
  settings      : settings from ${ZHENSA_SETTINGS_PATH}
  uwsgi         : Zhensa's uWSGI app ${ZHENSA_UWSGI_APP}
  nginx         : HTTP site ${NGINX_APPS_AVAILABLE}/${NGINX_ZHENSA_SITE}
  apache        : HTTP site ${APACHE_SITES_AVAILABLE}/${APACHE_ZHENSA_SITE}
install:
  valkey        : install a local valkey server
remove:
  redis         : remove a local redis server ${REDIS_HOME}/run/redis.sock
install:
  zhensa-src   : clone ${GIT_URL} into ${ZHENSA_SRC}
  packages      : installs packages from OS package manager required by Zhensa
  buildhost     : installs packages from OS package manager required by a Zhensa buildhost
instance:
  update        : update Zhensa instance (git fetch + reset & update settings.yml)
  check         : run checks from utils/zhensa_check.py in the active installation
  inspect       : run some small tests and inspect Zhensa's server status and log
  get_setting   : get settings value from running Zhensa instance
  cmd           : run command in Zhensa instance's environment (e.g. bash)
EOF
    zhensa.instance.env
    [[ -n ${1} ]] && err_msg "$1"
}

zhensa.instance.env() {
    echo "uWSGI:"
    if [[ ${ZHENSA_UWSGI_USE_SOCKET} == true ]]; then
        echo "  ZHENSA_UWSGI_SOCKET : ${ZHENSA_UWSGI_SOCKET}"
    else
        echo "  ZHENSA_INTERNAL_HTTP: ${ZHENSA_INTERNAL_HTTP}"
    fi
    cat <<EOF
environment:
  GIT_URL              : ${GIT_URL}
  GIT_BRANCH           : ${GIT_BRANCH}
  ZHENSA_URL          : ${ZHENSA_URL}
  ZHENSA_PORT         : ${ZHENSA_PORT}
  ZHENSA_BIND_ADDRESS : ${ZHENSA_BIND_ADDRESS}
EOF
}

main() {
    case $1 in
        install | remove | instance)
            nginx_distro_setup
            apache_distro_setup
            uWSGI_distro_setup
            required_commands \
                sudo systemctl install git wget curl ||
                exit
            ;;
    esac

    local _usage="unknown or missing $1 command $2"

    case $1 in
        --getenv)
            var="$2"
            echo "${!var}"
            exit 0
            ;;
        --cmd)
            shift
            "$@"
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        install)
            sudo_or_exit
            case $2 in
                all) zhensa.install.all ;;
                user) zhensa.install.user ;;
                pyenv) zhensa.install.pyenv ;;
                zhensa-src) zhensa.install.clone ;;
                settings) zhensa.install.settings ;;
                uwsgi) zhensa.install.uwsgi ;;
                packages) zhensa.install.packages ;;
                buildhost) zhensa.install.buildhost ;;
                nginx) zhensa.nginx.install ;;
                apache) zhensa.apache.install ;;
                valkey) zhensa.install.valkey ;;
                *)
                    usage "$_usage"
                    exit 42
                    ;;
            esac
            ;;
        remove)
            sudo_or_exit
            case $2 in
                all) zhensa.remove.all ;;
                user) drop_service_account "${SERVICE_USER}" ;;
                pyenv) zhensa.remove.pyenv ;;
                settings) zhensa.remove.settings ;;
                uwsgi) zhensa.remove.uwsgi ;;
                apache) zhensa.apache.remove ;;
                remove) zhensa.nginx.remove ;;
                valkey) zhensa.remove.valkey ;;
                redis) zhensa.remove.redis ;;
                *)
                    usage "$_usage"
                    exit 42
                    ;;
            esac
            ;;
        instance)
            case $2 in
                update)
                    sudo_or_exit
                    zhensa.instance.update
                    ;;
                check)
                    sudo_or_exit
                    zhensa.instance.self.call zhensa.check
                    ;;
                inspect)
                    sudo_or_exit
                    zhensa.instance.inspect
                    ;;
                cmd)
                    sudo_or_exit
                    shift
                    shift
                    zhensa.instance.exec "$@"
                    ;;
                get_setting)
                    shift
                    shift
                    zhensa.instance.get_setting "$@"
                    ;;
                call)
                    # call a function in instance's environment
                    shift
                    shift
                    zhensa.instance.self.call "$@"
                    ;;
                _call)
                    shift
                    shift
                    "$@"
                    ;;
                *)
                    usage "$_usage"
                    exit 42
                    ;;
            esac
            ;;
        *)
            local cmd="$1"
            _type="$(type -t "$cmd")"
            if [ "$_type" != 'function' ]; then
                usage "unknown or missing command $1"
                exit 42
            else
                "$cmd" "$@"
            fi
            ;;
    esac
}

zhensa.install.all() {
    rst_title "Zhensa installation" part

    local valkey_url

    rst_title "Zhensa"
    zhensa.install.packages
    wait_key 10
    zhensa.install.user
    wait_key 10
    zhensa.install.clone
    wait_key
    zhensa.install.pyenv
    wait_key
    zhensa.install.settings
    wait_key
    zhensa.instance.localtest
    wait_key
    zhensa.install.uwsgi
    wait_key

    rst_title "Valkey DB"
    zhensa.install.valkey.db

    rst_title "HTTP Server"
    zhensa.install.http.site

    rst_title "Finalize installation"
    if ask_yn "Do you want to run some checks?" Yn; then
        zhensa.instance.self.call zhensa.check
    fi
}

zhensa.install.valkey.db() {
    local valkey_url

    valkey_url=$(zhensa.instance.get_setting valkey.url)

    if [ "${valkey_url}" = "False" ]; then
        rst_para "valkey DB connector is not configured in your instance"
    else
        rst_para "\
In your instance, valkey DB connector is configured at:

    ${valkey_url}
"
        if zhensa.instance.exec python -c "from zhensa import valkeydb; valkeydb.initialize() or exit(42)"; then
            info_msg "Zhensa instance is able to connect valkey DB."
            return
        fi
    fi

    if ! [[ ${valkey_url} = valkey://localhost:6379/* ]]; then
        err_msg "Zhensa instance can't connect valkey DB / check valkey & your settings"
        return
    fi
    rst_para ".. but this valkey DB is not installed yet."

    if ask_yn "Do you want to install the valkey DB now?" Yn; then
        zhensa.install.valkey
        uWSGI_restart "$ZHENSA_UWSGI_APP"
    fi
}

zhensa.install.http.site() {

    if apache_is_installed; then
        info_msg "Apache is installed on this host."
        if ask_yn "Do you want to install a reverse proxy" Yn; then
            zhensa.apache.install
        fi
    elif nginx_is_installed; then
        info_msg "Nginx is installed on this host."
        if ask_yn "Do you want to install a reverse proxy" Yn; then
            zhensa.nginx.install
        fi
    else
        info_msg "Don't forget to install HTTP site."
    fi
}

zhensa.remove.all() {
    local valkey_url

    rst_title "De-Install Zhensa (service)"
    if ! ask_yn "Do you really want to deinstall Zhensa?"; then
        return
    fi

    valkey_url=$(zhensa.instance.get_setting valkey.url)
    if ! [[ ${valkey_url} = unix://${VALKEY_HOME}/run/valkey.sock* ]]; then
        zhensa.remove.valkey
    fi

    zhensa.remove.uwsgi
    drop_service_account "${SERVICE_USER}"
    zhensa.remove.settings
    wait_key

    if service_is_available "${ZHENSA_URL}"; then
        MSG="** Don't forget to remove your public site! (${ZHENSA_URL}) **" wait_key 10
    fi
}

zhensa.install.user() {
    rst_title "Zhensa -- install user" section
    echo
    if getent passwd "${SERVICE_USER}" >/dev/null; then
        echo "user already exists"
        return 0
    fi

    tee_stderr 1 <<EOF | bash | prefix_stdout
useradd --shell /bin/bash --system \
 --home-dir "${SERVICE_HOME}" \
 --comment 'Privacy-respecting metasearch engine' ${SERVICE_USER}
mkdir "${SERVICE_HOME}"
chown -R "${SERVICE_GROUP}:${SERVICE_GROUP}" "${SERVICE_HOME}"
groups ${SERVICE_USER}
EOF
}

zhensa.install.packages() {
    TITLE="Zhensa -- install packages" pkg_install "${ZHENSA_PACKAGES}"
}

zhensa.install.buildhost() {
    TITLE="Zhensa -- install buildhost packages" pkg_install \
        "${ZHENSA_PACKAGES} ${ZHENSA_BUILD_PACKAGES}"
}

zhensa.install.clone() {
    rst_title "Clone Zhensa sources" section
    if ! service_account_is_available "${SERVICE_USER}"; then
        die 42 "To clone Zhensa, first install user ${SERVICE_USER}."
    fi
    echo
    if ! sudo -i -u "${SERVICE_USER}" ls -d "$REPO_ROOT" >/dev/null; then
        die 42 "user '${SERVICE_USER}' missed read permission: $REPO_ROOT"
    fi
    # SERVICE_HOME="$(sudo -i -u "${SERVICE_USER}" echo \$HOME 2>/dev/null)"
    if [[ ! "${SERVICE_HOME}" ]]; then
        err_msg "to clone Zhensa sources, user ${SERVICE_USER} hast to be created first"
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
    # export SERVICE_HOME

    # clone repo and add a safe.directory entry to git's system config / see
    # https://github.com/zhenbah/zhensa/issues/1251
    git config --system --add safe.directory "${REPO_ROOT}/.git"
    git_clone "$REPO_ROOT" "${ZHENSA_SRC}" \
        "$GIT_BRANCH" "${SERVICE_USER}"
    git config --system --add safe.directory "${ZHENSA_SRC}"

    pushd "${ZHENSA_SRC}" >/dev/null
    tee_stderr 0.1 <<EOF | sudo -H -u "${SERVICE_USER}" -i 2>&1 | prefix_stdout "$_service_prefix"
cd "${ZHENSA_SRC}"
git remote set-url origin ${GIT_URL}
git config user.email "${ADMIN_EMAIL}"
git config user.name "${ADMIN_NAME}"
git config --list
EOF
    popd >/dev/null
}

zhensa.install.link_src() {
    rst_title "link Zhensa's sources to: $2" chapter
    echo
    tee_stderr 0.1 <<EOF | sudo -H -u "${SERVICE_USER}" -i 2>&1 | prefix_stdout "$_service_prefix"
mv -f "${ZHENSA_SRC}" "${ZHENSA_SRC}.backup"
ln -s "${2}" "${ZHENSA_SRC}"
ls -ld /usr/local/zhensa/zhensa-src
EOF
    echo
    uWSGI_restart "$ZHENSA_UWSGI_APP"
}

zhensa.install.pyenv() {
    rst_title "Create virtualenv (python)" section
    echo
    if [[ ! -f "${ZHENSA_SRC}/manage" ]]; then
        die 42 "To create pyenv for Zhensa, first install zhensa-src."
    fi
    info_msg "create pyenv in ${ZHENSA_PYENV}"
    tee_stderr 0.1 <<EOF | sudo -H -u "${SERVICE_USER}" -i 2>&1 | prefix_stdout "$_service_prefix"
rm -rf "${ZHENSA_PYENV}"
python -m venv "${ZHENSA_PYENV}"
grep -qFs -- 'source ${ZHENSA_PYENV}/bin/activate' ~/.profile \
  || echo 'source ${ZHENSA_PYENV}/bin/activate' >> ~/.profile
EOF
    info_msg "inspect python's virtual environment"
    tee_stderr 0.1 <<EOF | sudo -H -u "${SERVICE_USER}" -i 2>&1 | prefix_stdout "$_service_prefix"
command -v python && python --version
EOF
    wait_key
    info_msg "install needed python packages"
    tee_stderr 0.1 <<EOF | sudo -H -u "${SERVICE_USER}" -i 2>&1 | prefix_stdout "$_service_prefix"
pip install -U pip
pip install -U setuptools
pip install -U wheel
pip install -U pyyaml
cd ${ZHENSA_SRC}
pip install --use-pep517 --no-build-isolation -e .
EOF
}

zhensa.remove.pyenv() {
    rst_title "Remove virtualenv (python)" section
    if ! ask_yn "Do you really want to drop ${ZHENSA_PYENV} ?"; then
        return
    fi
    info_msg "remove pyenv activation from ~/.profile"
    tee_stderr 0.1 <<EOF | sudo -H -u "${SERVICE_USER}" -i 2>&1 | prefix_stdout "$_service_prefix"
grep -v 'source ${ZHENSA_PYENV}/bin/activate' ~/.profile > ~/.profile.##
mv ~/.profile.## ~/.profile
EOF
    rm -rf "${ZHENSA_PYENV}"
}

zhensa.install.settings() {
    rst_title "install ${ZHENSA_SETTINGS_PATH}" section

    if ! [[ -f "${ZHENSA_SRC}/.git/config" ]]; then
        die "Before install settings, first install Zhensa."
    fi

    mkdir -p "$(dirname "${ZHENSA_SETTINGS_PATH}")"

    DEFAULT_SELECT=1 \
        install_template --no-eval \
        "${ZHENSA_SETTINGS_PATH}" \
        "${SERVICE_USER}" "${SERVICE_GROUP}"

    tee_stderr 0.1 <<EOF | sudo -H -i 2>&1 | prefix_stdout "root"
sed -i -e "s/ultrasecretkey/$(openssl rand -hex 16)/g" "${ZHENSA_SETTINGS_PATH}"
EOF
}

zhensa.remove.settings() {
    rst_title "remove ${ZHENSA_SETTINGS_PATH}" section
    if ask_yn "Do you want to delete the Zhensa settings?" Yn; then
        rm -f "${ZHENSA_SETTINGS_PATH}"
    fi
}

zhensa.check() {
    rst_title "Zhensa checks" section
    "${ZHENSA_PYENV}/bin/python" "${ZHENSA_SRC}/utils/zhensa_check.py"
}

zhensa.instance.update() {
    rst_title "Update Zhensa instance"
    rst_para "fetch from $GIT_URL and reset to origin/$GIT_BRANCH"
    tee_stderr 0.3 <<EOF | sudo -H -u "${SERVICE_USER}" -i 2>&1 | prefix_stdout "$_service_prefix"
cd ${ZHENSA_SRC}
git fetch origin "$GIT_BRANCH"
git reset --hard "origin/$GIT_BRANCH"
pip install -U pip
pip install -U setuptools
pip install -U wheel
pip install -U pyyaml
pip install -U --use-pep517 --no-build-isolation -e .
EOF
    rst_para "update instance's settings.yml from ${ZHENSA_SETTINGS_PATH}"
    DEFAULT_SELECT=2 \
        install_template --no-eval \
        "${ZHENSA_SETTINGS_PATH}" \
        "${SERVICE_USER}" "${SERVICE_GROUP}"

    sudo -H -i <<EOF
sed -i -e "s/ultrasecretkey/$(openssl rand -hex 16)/g" "${ZHENSA_SETTINGS_PATH}"
EOF
    uWSGI_restart "${ZHENSA_UWSGI_APP}"
}

zhensa.install.uwsgi() {
    rst_title "Zhensa (install uwsgi)"
    install_uwsgi
    if [[ ${ZHENSA_UWSGI_USE_SOCKET} == true ]]; then
        zhensa.install.uwsgi.socket
    else
        zhensa.install.uwsgi.http
    fi
}

zhensa.install.uwsgi.http() {
    rst_para "Install ${ZHENSA_UWSGI_APP} at: http://${ZHENSA_INTERNAL_HTTP}"
    uWSGI_install_app "${ZHENSA_UWSGI_APP}"
    if ! zhensa.uwsgi.available; then
        err_msg "URL http://${ZHENSA_INTERNAL_HTTP} not available, check Zhensa & uwsgi setup!"
    fi
}

zhensa.install.uwsgi.socket() {
    rst_para "Install ${ZHENSA_UWSGI_APP} using socket at: ${ZHENSA_UWSGI_SOCKET}"
    mkdir -p "$(dirname "${ZHENSA_UWSGI_SOCKET}")"
    chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "$(dirname "${ZHENSA_UWSGI_SOCKET}")"

    case $DIST_ID-$DIST_VERS in
        fedora-*)
            # Fedora runs uWSGI in emperor-tyrant mode: in Tyrant mode the
            # Emperor will run the vassal using the UID/GID of the vassal
            # configuration file [1] (user and group of the app .ini file).
            # [1] https://uwsgi-docs.readthedocs.io/en/latest/Emperor.html#tyrant-mode-secure-multi-user-hosting
            uWSGI_install_app --variant=socket "${ZHENSA_UWSGI_APP}" "${SERVICE_USER}" "${SERVICE_GROUP}"
            ;;
        *)
            uWSGI_install_app --variant=socket "${ZHENSA_UWSGI_APP}"
            ;;
    esac
    sleep 5
    if ! zhensa.uwsgi.available; then
        err_msg "uWSGI socket not available at: ${ZHENSA_UWSGI_SOCKET}"
    fi
}

zhensa.uwsgi.available() {
    if [[ ${ZHENSA_UWSGI_USE_SOCKET} == true ]]; then
        [[ -S "${ZHENSA_UWSGI_SOCKET}" ]]
        exit_val=$?
        if [[ $exit_val = 0 ]]; then
            info_msg "uWSGI socket is located at: ${ZHENSA_UWSGI_SOCKET}"
        fi
    else
        service_is_available "http://${ZHENSA_INTERNAL_HTTP}"
        exit_val=$?
    fi
    return "$exit_val"
}

zhensa.remove.uwsgi() {
    rst_title "Remove Zhensa's uWSGI app (${ZHENSA_UWSGI_APP})" section
    echo
    uWSGI_remove_app "${ZHENSA_UWSGI_APP}"
}

zhensa.remove.redis() {
    rst_title "Zhensa (remove redis)"
    redis.rmgrp "${SERVICE_USER}"
    redis.remove
}

zhensa.install.valkey() {
    rst_title "Zhensa (install valkey)"
    valkey.install
}

zhensa.instance.localtest() {
    rst_title "Test Zhensa instance locally" section
    rst_para "Activate debug mode, start a minimal Zhensa " \
        "service and debug a HTTP request/response cycle."

    if service_is_available "http://${ZHENSA_INTERNAL_HTTP}" &>/dev/null; then
        err_msg "URL/port http://${ZHENSA_INTERNAL_HTTP} is already in use, you"
        err_msg "should stop that service before starting local tests!"
        if ! ask_yn "Continue with local tests?"; then
            return
        fi
    fi
    echo
    zhensa.instance.debug.on
    tee_stderr 0.1 <<EOF | sudo -H -u "${SERVICE_USER}" -i 2>&1 | prefix_stdout "$_service_prefix"
export ZHENSA_SETTINGS_PATH="${ZHENSA_SETTINGS_PATH}"
cd ${ZHENSA_SRC}
timeout 10 python zhensa/webapp.py &
sleep 3
curl --location --verbose --head --insecure ${ZHENSA_INTERNAL_HTTP}
EOF
    echo
    zhensa.instance.debug.off
}

zhensa.install.http.pre() {
    if ! zhensa.uwsgi.available; then
        rst_para "\
To install uWSGI use::

    $(basename "$0") install uwsgi
"
        die 42 "Zhensa's uWSGI app not available"
    fi

    if ! zhensa.instance.exec python -c "from zhensa import valkeydb; valkeydb.initialize() or exit(42)"; then
        rst_para "\
The configured valkey DB is not available: If your server is public to the
internet, you should setup a bot protection to block excessively bot queries.
Bot protection requires a valkey DB.  About bot protection visit the official
Zhensa documentation and query for the word 'limiter'.
"
    fi
}

zhensa.apache.install() {
    rst_title "Install Apache site ${APACHE_ZHENSA_SITE}"
    rst_para "\
This installs Zhensa's uWSGI app as apache site.  The apache site is located at:
${APACHE_SITES_AVAILABLE}/${APACHE_ZHENSA_SITE}."
    zhensa.install.http.pre

    if ! apache_is_installed; then
        err_msg "Apache packages are not installed"
        if ! ask_yn "Do you really want to continue and install apache packages?" Yn; then
            return
        else
            FORCE_SELECTION=Y install_apache
        fi
    else
        info_msg "Apache packages are installed [OK]"
    fi

    if [[ ${ZHENSA_UWSGI_USE_SOCKET} == true ]]; then
        apache_install_site --variant=socket "${APACHE_ZHENSA_SITE}"
    else
        apache_install_site "${APACHE_ZHENSA_SITE}"
    fi

    if ! service_is_available "${ZHENSA_URL}"; then
        err_msg "Public service at ${ZHENSA_URL} is not available!"
    fi
}

zhensa.apache.remove() {
    rst_title "Remove Apache site ${APACHE_ZHENSA_SITE}"
    rst_para "\
This removes apache site ${APACHE_ZHENSA_SITE}::

  ${APACHE_SITES_AVAILABLE}/${APACHE_ZHENSA_SITE}"

    ! apache_is_installed && err_msg "Apache is not installed."
    if ! ask_yn "Do you really want to continue?" Yn; then
        return
    fi
    apache_remove_site "${APACHE_ZHENSA_SITE}"
}

zhensa.nginx.install() {

    rst_title "Install nginx site ${NGINX_ZHENSA_SITE}"
    rst_para "\
This installs Zhensa's uWSGI app as Nginx site.  The Nginx site is located at:
${NGINX_APPS_AVAILABLE}/${NGINX_ZHENSA_SITE} and requires a uWSGI."
    zhensa.install.http.pre

    if ! nginx_is_installed; then
        err_msg "Nginx packages are not installed"
        if ! ask_yn "Do you really want to continue and install Nginx packages?" Yn; then
            return
        else
            FORCE_SELECTION=Y install_nginx
        fi
    else
        info_msg "Nginx packages are installed [OK]"
    fi

    if [[ ${ZHENSA_UWSGI_USE_SOCKET} == true ]]; then
        nginx_install_app --variant=socket "${NGINX_ZHENSA_SITE}"
    else
        nginx_install_app "${NGINX_ZHENSA_SITE}"
    fi

    if ! service_is_available "${ZHENSA_URL}"; then
        err_msg "Public service at ${ZHENSA_URL} is not available!"
    fi
}

zhensa.nginx.remove() {
    rst_title "Remove Nginx site ${NGINX_ZHENSA_SITE}"
    rst_para "\
This removes Nginx site ${NGINX_ZHENSA_SITE}::

  ${NGINX_APPS_AVAILABLE}/${NGINX_ZHENSA_SITE}"

    ! nginx_is_installed && err_msg "Nginx is not installed."
    if ! ask_yn "Do you really want to continue?" Yn; then
        return
    fi
    nginx_remove_app "${NGINX_ZHENSA_SITE}"
}

zhensa.instance.exec() {
    if ! service_account_is_available "${SERVICE_USER}"; then
        die 42 "can't execute: instance does not exist (missed account ${SERVICE_USER})"
    fi
    sudo -H -i -u "${SERVICE_USER}" \
        ZHENSA_UWSGI_USE_SOCKET="${ZHENSA_UWSGI_USE_SOCKET}" \
        "$@"
}

zhensa.instance.self.call() {
    # wrapper to call a function in instance's environment
    info_msg "wrapper:  utils/zhensa.sh instance _call $*"
    zhensa.instance.exec "${ZHENSA_SRC}/utils/zhensa.sh" instance _call "$@"
}

zhensa.instance.get_setting() {
    zhensa.instance.exec python <<EOF
from zhensa import get_setting
print(get_setting('$1'))
EOF
}

zhensa.instance.debug.on() {
    warn_msg "Do not enable debug in a production environment!"
    info_msg "try to enable debug mode ..."
    tee_stderr 0.1 <<EOF | sudo -H -i 2>&1 | prefix_stdout "$_service_prefix"
cd ${ZHENSA_SRC}
sed -i -e "s/debug: false/debug: true/g" "$ZHENSA_SETTINGS_PATH"
EOF
    uWSGI_restart "$ZHENSA_UWSGI_APP"
}

zhensa.instance.debug.off() {
    info_msg "try to disable debug mode ..."
    tee_stderr 0.1 <<EOF | sudo -H -i 2>&1 | prefix_stdout "$_service_prefix"
cd ${ZHENSA_SRC}
sed -i -e "s/debug: true/debug: false/g" "$ZHENSA_SETTINGS_PATH"
EOF
    uWSGI_restart "$ZHENSA_UWSGI_APP"
}

zhensa.instance.inspect() {
    rst_title "Inspect Zhensa instance"
    echo

    zhensa.instance.self.call _zhensa.instance.inspect

    local _debug_on
    if ask_yn "Enable Zhensa debug mode?"; then
        zhensa.instance.debug.on
        _debug_on=1
    fi
    echo

    case $DIST_ID-$DIST_VERS in
        ubuntu-* | debian-*)
            # For uWSGI debian uses the LSB init process; for each configuration
            # file new uWSGI daemon instance is started with additional option.
            service uwsgi status "${SERVICE_NAME}"
            ;;
        arch-*)
            systemctl --no-pager -l status "uwsgi@${SERVICE_NAME%.*}"
            ;;
        fedora-*)
            systemctl --no-pager -l status uwsgi
            ;;
    esac

    echo -e "// use ${_BCyan}CTRL-C${_creset} to stop monitoring the log"
    read -r -s -n1 -t 5
    echo

    while true; do
        trap break 2
        case $DIST_ID-$DIST_VERS in
            ubuntu-* | debian-*) tail -f "/var/log/uwsgi/app/${SERVICE_NAME%.*}.log" ;;
            arch-*) journalctl -f -u "uwsgi@${SERVICE_NAME%.*}" ;;
            fedora-*) journalctl -f -u uwsgi ;;
        esac
    done

    if [[ $_debug_on == 1 ]]; then
        zhensa.instance.debug.off
    fi
    return 0
}

_zhensa.instance.inspect() {
    zhensa.instance.env

    MSG="${_Green}[${_BCyan}CTRL-C${_Green}] to stop or [${_BCyan}KEY${_Green}] to continue${_creset}"

    if ! zhensa.uwsgi.available; then
        err_msg "Zhensa's uWSGI app not available"
        wait_key
    fi
    if ! service_is_available "${ZHENSA_URL}"; then
        err_msg "Public service at ${ZHENSA_URL} is not available!"
        wait_key
    fi
}

zhensa.doc.rst() {

    local APACHE_SITES_AVAILABLE="/etc/apache2/sites-available"
    local NGINX_APPS_AVAILABLE="/etc/nginx/default.apps-available"

    local debian="${ZHENSA_PACKAGES_debian}"
    local arch="${ZHENSA_PACKAGES_arch}"
    local fedora="${ZHENSA_PACKAGES_fedora}"
    local debian_build="${ZHENSA_BUILD_PACKAGES_debian}"
    local arch_build="${ZHENSA_BUILD_PACKAGES_arch}"
    local fedora_build="${ZHENSA_BUILD_PACKAGES_fedora}"
    debian="$(echo "${debian}" | sed 's/.*/          & \\/' | sed '$ s/.$//')"
    arch="$(echo "${arch}" | sed 's/.*/          & \\/' | sed '$ s/.$//')"
    fedora="$(echo "${fedora}" | sed 's/.*/          & \\/' | sed '$ s/.$//')"
    debian_build="$(echo "${debian_build}" | sed 's/.*/          & \\/' | sed '$ s/.$//')"
    arch_build="$(echo "${arch_build}" | sed 's/.*/          & \\/' | sed '$ s/.$//')"
    fedora_build="$(echo "${fedora_build}" | sed 's/.*/          & \\/' | sed '$ s/.$//')"

    if [[ ${ZHENSA_UWSGI_USE_SOCKET} == true ]]; then
        uwsgi_variant=':socket'
    else
        uwsgi_variant=':socket'
    fi

    eval "echo \"$(<"${REPO_ROOT}/docs/build-templates/zhensa.rst")\""

    # I use ubuntu-20.04 here to demonstrate that versions are also supported,
    # normally debian-* and ubuntu-* are most the same.

    for DIST_NAME in ubuntu-20.04 arch fedora; do
        (
            DIST_ID=${DIST_NAME%-*}
            DIST_VERS=${DIST_NAME#*-}
            [[ $DIST_VERS =~ $DIST_ID ]] && DIST_VERS=
            uWSGI_distro_setup

            echo -e "\n.. START zhensa uwsgi-description $DIST_NAME"

            case $DIST_ID-$DIST_VERS in
                ubuntu-* | debian-*)
                    cat <<EOF

.. code:: bash

   # init.d --> /usr/share/doc/uwsgi/README.Debian.gz
   # For uWSGI debian uses the LSB init process, this might be changed
   # one day, see https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=833067

   create     ${uWSGI_APPS_AVAILABLE}/${ZHENSA_UWSGI_APP}
   enable:    sudo -H ln -s ${uWSGI_APPS_AVAILABLE}/${ZHENSA_UWSGI_APP} ${uWSGI_APPS_ENABLED}/
   start:     sudo -H service uwsgi start   ${ZHENSA_UWSGI_APP%.*}
   restart:   sudo -H service uwsgi restart ${ZHENSA_UWSGI_APP%.*}
   stop:      sudo -H service uwsgi stop    ${ZHENSA_UWSGI_APP%.*}
   disable:   sudo -H rm ${uWSGI_APPS_ENABLED}/${ZHENSA_UWSGI_APP}

EOF
                    ;;
                arch-*)
                    cat <<EOF

.. code:: bash

   # systemd --> /usr/lib/systemd/system/uwsgi@.service
   # For uWSGI archlinux uses systemd template units, see
   # - http://0pointer.de/blog/projects/instances.html
   # - https://uwsgi-docs.readthedocs.io/en/latest/Systemd.html#one-service-per-app-in-systemd

   create:    ${uWSGI_APPS_ENABLED}/${ZHENSA_UWSGI_APP}
   enable:    sudo -H systemctl enable   uwsgi@${ZHENSA_UWSGI_APP%.*}
   start:     sudo -H systemctl start    uwsgi@${ZHENSA_UWSGI_APP%.*}
   restart:   sudo -H systemctl restart  uwsgi@${ZHENSA_UWSGI_APP%.*}
   stop:      sudo -H systemctl stop     uwsgi@${ZHENSA_UWSGI_APP%.*}
   disable:   sudo -H systemctl disable  uwsgi@${ZHENSA_UWSGI_APP%.*}

EOF
                    ;;
                fedora-* | centos-7)
                    cat <<EOF

.. code:: bash

   # systemd --> /usr/lib/systemd/system/uwsgi.service
   # The unit file starts uWSGI in emperor mode (/etc/uwsgi.ini), see
   # - https://uwsgi-docs.readthedocs.io/en/latest/Emperor.html

   create:    ${uWSGI_APPS_ENABLED}/${ZHENSA_UWSGI_APP}
   restart:   sudo -H touch ${uWSGI_APPS_ENABLED}/${ZHENSA_UWSGI_APP}
   disable:   sudo -H rm ${uWSGI_APPS_ENABLED}/${ZHENSA_UWSGI_APP}

EOF
                    ;;
            esac
            echo -e ".. END zhensa uwsgi-description $DIST_NAME"

            local _show_cursor="" # prevent from prefix_stdout's trailing show-cursor

            echo -e "\n.. START zhensa uwsgi-appini $DIST_NAME"
            echo ".. code:: bash"
            echo
            eval "echo \"$(<"${TEMPLATES}/${uWSGI_APPS_AVAILABLE}/${ZHENSA_UWSGI_APP}${uwsgi_variant}")\"" | prefix_stdout "  "
            echo -e "\n.. END zhensa uwsgi-appini $DIST_NAME"

            echo -e "\n.. START nginx socket"
            echo ".. code:: nginx"
            echo
            eval "echo \"$(<"${TEMPLATES}/${NGINX_APPS_AVAILABLE}/${NGINX_ZHENSA_SITE}:socket")\"" | prefix_stdout "  "
            echo -e "\n.. END nginx socket"

            echo -e "\n.. START nginx http"
            echo ".. code:: nginx"
            echo
            eval "echo \"$(<"${TEMPLATES}/${NGINX_APPS_AVAILABLE}/${NGINX_ZHENSA_SITE}")\"" | prefix_stdout "  "
            echo -e "\n.. END nginx http"

            echo -e "\n.. START apache socket"
            echo ".. code:: apache"
            echo
            eval "echo \"$(<"${TEMPLATES}/${APACHE_SITES_AVAILABLE}/${APACHE_ZHENSA_SITE}:socket")\"" | prefix_stdout "  "
            echo -e "\n.. END apache socket"

            echo -e "\n.. START apache http"
            echo ".. code:: apache"
            echo
            eval "echo \"$(<"${TEMPLATES}/${APACHE_SITES_AVAILABLE}/${APACHE_ZHENSA_SITE}")\"" | prefix_stdout "  "
            echo -e "\n.. END apache http"
        )
    done

}

# ----------------------------------------------------------------------------
main "$@"
# ----------------------------------------------------------------------------
