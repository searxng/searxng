#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# shellcheck disable=SC2001

# Script options from the environment:
SEARXNG_UWSGI_USE_SOCKET="${SEARXNG_UWSGI_USE_SOCKET:-true}"

# shellcheck source=utils/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
# shellcheck source=utils/lib_redis.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib_redis.sh"
# shellcheck source=utils/brand.env
source "${REPO_ROOT}/utils/brand.env"

SERVICE_NAME="searxng"
SERVICE_USER="searxng"
SERVICE_HOME="/usr/local/searxng"
SERVICE_GROUP="searxng"

SEARXNG_SRC="${SERVICE_HOME}/searxng-src"
# shellcheck disable=SC2034
SEARXNG_STATIC="${SEARXNG_SRC}/searx/static"

SEARXNG_PYENV="${SERVICE_HOME}/searx-pyenv"
SEARXNG_SETTINGS_PATH="/etc/searxng/settings.yml"
SEARXNG_UWSGI_APP="searxng.ini"

SEARXNG_INTERNAL_HTTP="${SEARXNG_BIND_ADDRESS}:${SEARXNG_PORT}"
if [[ ${SEARXNG_UWSGI_USE_SOCKET} == true ]]; then
    SEARXNG_UWSGI_SOCKET="${SERVICE_HOME}/run/socket"
else
    SEARXNG_UWSGI_SOCKET=
fi

# SEARXNG_URL: the public URL of the instance (https://example.org/searxng).  The
# value is taken from environment ${SEARXNG_URL} in ./utils/brand.env.  This
# variable is an empty string if server.base_url in the settings.yml is set to
# 'false'.

SEARXNG_URL="${SEARXNG_URL:-http://$(uname -n)/searxng}"
SEARXNG_URL="${SEARXNG_URL%/}" # if exists, remove trailing slash
if in_container; then
    # hint: Linux containers do not have DNS entries, lets use IPs
    SEARXNG_URL="http://$(primary_ip)/searxng"
fi
SEARXNG_URL_PATH="$(echo "${SEARXNG_URL}" | sed -e 's,^.*://[^/]*\(/.*\),\1,g')"
[[ "${SEARXNG_URL_PATH}" == "${SEARXNG_URL}" ]] && SEARXNG_URL_PATH=/

# Apache settings

APACHE_SEARXNG_SITE="searxng.conf"

# nginx settings

NGINX_SEARXNG_SITE="searxng.conf"

# apt packages

SEARXNG_PACKAGES_debian="\
python3-dev python3-babel python3-venv
uwsgi uwsgi-plugin-python3
git build-essential libxslt-dev zlib1g-dev libffi-dev libssl-dev"

SEARXNG_BUILD_PACKAGES_debian="\
firefox graphviz imagemagick texlive-xetex librsvg2-bin
texlive-latex-recommended texlive-extra-utils fonts-dejavu
latexmk shellcheck"

# pacman packages

SEARXNG_PACKAGES_arch="\
python python-pip python-lxml python-babel
uwsgi uwsgi-plugin-python
git base-devel libxml2"

SEARXNG_BUILD_PACKAGES_arch="\
firefox graphviz imagemagick texlive-bin extra/librsvg
texlive-core texlive-latexextra ttf-dejavu shellcheck"

# dnf packages

SEARXNG_PACKAGES_fedora="\
python python-pip python-lxml python-babel python3-devel
uwsgi uwsgi-plugin-python3
git @development-tools libxml2 openssl"

SEARXNG_BUILD_PACKAGES_fedora="\
firefox graphviz graphviz-gd ImageMagick librsvg2-tools
texlive-xetex-bin texlive-collection-fontsrecommended
texlive-collection-latex dejavu-sans-fonts dejavu-serif-fonts
dejavu-sans-mono-fonts ShellCheck"

case $DIST_ID-$DIST_VERS in
    ubuntu-18.04)
        SEARXNG_PACKAGES="${SEARXNG_PACKAGES_debian}"
        SEARXNG_BUILD_PACKAGES="${SEARXNG_BUILD_PACKAGES_debian}"
        APACHE_PACKAGES="$APACHE_PACKAGES libapache2-mod-proxy-uwsgi"
        ;;
    ubuntu-20.04)
        # https://wiki.ubuntu.com/FocalFossa/ReleaseNotes#Python3_by_default
        SEARXNG_PACKAGES="${SEARXNG_PACKAGES_debian} python-is-python3"
        SEARXNG_BUILD_PACKAGES="${SEARXNG_BUILD_PACKAGES_debian}"
        ;;
    ubuntu-*|debian-*)
        SEARXNG_PACKAGES="${SEARXNG_PACKAGES_debian}"
        SEARXNG_BUILD_PACKAGES="${SEARXNG_BUILD_PACKAGES_debian}"
        ;;
    arch-*)
        SEARXNG_PACKAGES="${SEARXNG_PACKAGES_arch}"
        SEARXNG_BUILD_PACKAGES="${SEARXNG_BUILD_PACKAGES_arch}"
        ;;
    fedora-*)
        SEARXNG_PACKAGES="${SEARXNG_PACKAGES_fedora}"
        SEARXNG_BUILD_PACKAGES="${SEARXNG_BUILD_PACKAGES_fedora}"
        ;;
esac

_service_prefix="  ${_Yellow}|${SERVICE_USER}|${_creset} "

# ----------------------------------------------------------------------------
usage() {
# ----------------------------------------------------------------------------

    # shellcheck disable=SC1117
    cat <<EOF
usage:
  $(basename "$0") install    [all|user|pyenv|settings|uwsgi|redis|nginx|apache|searxng-src|packages|buildhost]
  $(basename "$0") remove     [all|user|pyenv|settings|uwsgi|redis|nginx|apache]
  $(basename "$0") instance   [cmd|update|check|localtest|inspect]
install|remove:
  all           : complete (de-) installation of the SearXNG service
  user          : service user '${SERVICE_USER}' (${SERVICE_HOME})
  pyenv         : virtualenv (python) in ${SEARXNG_PYENV}
  settings      : settings from ${SEARXNG_SETTINGS_PATH}
  uwsgi         : SearXNG's uWSGI app ${SEARXNG_UWSGI_APP}
  redis         : build & install or remove a local redis server ${REDIS_HOME}/run/redis.sock
  nginx         : HTTP site ${NGINX_APPS_AVAILABLE}/${NGINX_SEARXNG_SITE}
  apache        : HTTP site ${APACHE_SITES_AVAILABLE}/${APACHE_SEARXNG_SITE}
install:
  searxng-src   : clone ${GIT_URL} into ${SEARXNG_SRC}
  packages      : installs packages from OS package manager required by SearXNG
  buildhost     : installs packages from OS package manager required by a SearXNG buildhost
instance:
  update        : update SearXNG instance (git fetch + reset & update settings.yml)
  check         : run checks from utils/searxng_check.py in the active installation
  inspect       : run some small tests and inspect SearXNG's server status and log
  get_setting   : get settings value from running SearXNG instance
  cmd           : run command in SearXNG instance's environment (e.g. bash)
EOF
    searxng.instance.env
    [[ -n ${1} ]] &&  err_msg "$1"
}

searxng.instance.env() {
    echo "uWSGI:"
    if [[ ${SEARXNG_UWSGI_USE_SOCKET} == true ]]; then
        echo "  SEARXNG_UWSGI_SOCKET : ${SEARXNG_UWSGI_SOCKET}"
    else
        echo "  SEARXNG_INTERNAL_HTTP: ${SEARXNG_INTERNAL_HTTP}"
    fi
    cat <<EOF
environment ${SEARXNG_SRC}/utils/brand.env:
  GIT_URL              : ${GIT_URL}
  GIT_BRANCH           : ${GIT_BRANCH}
  SEARXNG_URL          : ${SEARXNG_URL}
  SEARXNG_PORT         : ${SEARXNG_PORT}
  SEARXNG_BIND_ADDRESS : ${SEARXNG_BIND_ADDRESS}
EOF
}

main() {
    required_commands \
        sudo systemctl install git wget curl \
        || exit

    local _usage="unknown or missing $1 command $2"

    case $1 in
        --getenv)  var="$2"; echo "${!var}"; exit 0;;
        -h|--help) usage; exit 0;;
        install)
            sudo_or_exit
            case $2 in
                all) searxng.install.all;;
                user) searxng.install.user;;
                pyenv) searxng.install.pyenv;;
                searxng-src) searxng.install.clone;;
                settings) searxng.install.settings;;
                uwsgi) searxng.install.uwsgi;;
                packages) searxng.install.packages;;
                buildhost) searxng.install.buildhost;;
                nginx) searxng.nginx.install;;
                apache) searxng.apache.install;;
                redis) searxng.install.redis;;
                *) usage "$_usage"; exit 42;;
            esac
            ;;
        remove)
            sudo_or_exit
            case $2 in
                all) searxng.remove.all;;
                user) drop_service_account "${SERVICE_USER}";;
                pyenv) searxng.remove.pyenv;;
                settings) searxng.remove.settings;;
                uwsgi) searxng.remove.uwsgi;;
                apache) searxng.apache.remove;;
                remove) searxng.nginx.remove;;
                redis) searxng.remove.redis;;
                *) usage "$_usage"; exit 42;;
            esac
            ;;
        instance)
            case $2 in
                update)
                    sudo_or_exit
                    searxng.instance.update
                    ;;
                check)
                    sudo_or_exit
                    searxng.instance.self.call searxng.check
                    ;;
                inspect)
                    sudo_or_exit
                    searxng.instance.inspect
                    ;;
                cmd)
                    sudo_or_exit
                    shift; shift; searxng.instance.exec "$@"
                    ;;
                get_setting)
                    shift; shift; searxng.instance.get_setting "$@"
                    ;;
                call)
                    # call a function in instance's environment
                    shift; shift; searxng.instance.self.call "$@"
                    ;;
                _call)
                    shift; shift; "$@"
                    ;;
                *) usage "$_usage"; exit 42;;
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

searxng.install.all() {
    rst_title "SearXNG installation" part

    local redis_url

    rst_title "SearXNG"
    searxng.install.packages
    wait_key 10
    searxng.install.user
    wait_key 10
    searxng.install.clone
    wait_key
    searxng.install.pyenv
    wait_key
    searxng.install.settings
    wait_key
    searxng.instance.localtest
    wait_key
    searxng.install.uwsgi
    wait_key

    rst_title "Redis DB"
    searxng.install.redis.db

    rst_title "HTTP Server"
    searxng.install.http.site

    rst_title "Finalize installation"
    if ask_yn "Do you want to run some checks?" Yn; then
        searxng.instance.self.call searxng.check
    fi
}

searxng.install.redis.db() {
    local redis_url

    redis_url=$(searxng.instance.get_setting redis.url)
    rst_para "\
In your instance, redis DB connector is configured at:

    ${redis_url}
"
    if searxng.instance.exec python -c "from searx import redisdb; redisdb.initialize() or exit(42)"; then
        info_msg "SearXNG instance is able to connect redis DB."
        return
    fi
    if ! [[ ${redis_url} = unix://${REDIS_HOME}/run/redis.sock* ]]; then
        err_msg "SearXNG instance can't connect redis DB / check redis & your settings"
        return
    fi
    rst_para ".. but this redis DB is not installed yet."

    case $DIST_ID-$DIST_VERS in
        fedora-*)
            # Fedora runs uWSGI in emperor-tyrant mode: in Tyrant mode the
            # Emperor will run the vassal using the UID/GID of the vassal
            # configuration file [1] (user and group of the app .ini file).
            #
            # HINT: without option ``emperor-tyrant-initgroups=true`` in
            # ``/etc/uwsgi.ini`` the process won't get the additional groups,
            # but this option is not available in 2.0.x branch [2][3] / on
            # fedora35 there is v2.0.20 installed --> no way to get additional
            # groups on fedora's tyrant mode.
            #
            # ERROR:searx.redisdb: [searxng (993)] can't connect redis DB ...
            # ERROR:searx.redisdb:   Error 13 connecting to unix socket: /usr/local/searxng-redis/run/redis.sock. Permission denied.
            # ERROR:searx.plugins.limiter: init limiter DB failed!!!
            #
            # $ ps -aef | grep '/usr/sbin/uwsgi --ini searxng.ini'
            # searxng       93      92  0 12:43 ?        00:00:00 /usr/sbin/uwsgi --ini searxng.ini
            # searxng      186      93  0 12:44 ?        00:00:01 /usr/sbin/uwsgi --ini searxng.ini
            #
            # Additional groups:
            #
            # $ groups searxng
            # searxng : searxng searxng-redis
            #
            # Here you can see that the additional "Groups" of PID 186 are unset
            # (missing gid of searxng-redis)
            #
            # $ cat /proc/186/task/186/status
            # ...
            # Uid:      993     993     993     993
            # Gid:      993     993     993     993
            # FDSize:   128
            # Groups:
            # ...
            #
            # [1] https://uwsgi-docs.readthedocs.io/en/latest/Emperor.html#tyrant-mode-secure-multi-user-hosting
            # [2] https://github.com/unbit/uwsgi/issues/2099
            # [3] https://github.com/unbit/uwsgi/pull/752

            rst_para "\
Fedora uses emperor-tyrant mode / in this mode we had a lot of trouble with
sockets and permissions of the vasals.  We recommend to setup a redis DB
and using redis:// TCP protocol in the settings.yml configuration."
            ;;
        *)
            if ask_yn "Do you want to install the redis DB now?" Yn; then
                searxng.install.redis
                uWSGI_restart "$SEARXNG_UWSGI_APP"
            fi
            ;;
    esac
}

searxng.install.http.site() {

    if apache_is_installed; then
        info_msg "Apache is installed on this host."
        if ask_yn "Do you want to install a reverse proxy" Yn; then
            searxng.apache.install
        fi
    elif nginx_is_installed; then
        info_msg "Nginx is installed on this host."
        if ask_yn "Do you want to install a reverse proxy" Yn; then
            searxng.nginx.install
        fi
    else
        info_msg "Don't forget to install HTTP site."
    fi
}

searxng.remove.all() {
    local redis_url

    rst_title "De-Install SearXNG (service)"
    if ! ask_yn "Do you really want to deinstall SearXNG?"; then
        return
    fi

    redis_url=$(searxng.instance.get_setting redis.url)
    if ! [[ ${redis_url} = unix://${REDIS_HOME}/run/redis.sock* ]]; then
        searxng.remove.redis
    fi

    searxng.remove.uwsgi
    drop_service_account "${SERVICE_USER}"
    searxng.remove.settings
    wait_key

    if service_is_available "${SEARXNG_URL}"; then
        MSG="** Don't forget to remove your public site! (${SEARXNG_URL}) **" wait_key 10
    fi
}

searxng.install.user() {
    rst_title "SearXNG -- install user" section
    echo
    if getent passwd "${SERVICE_USER}"  > /dev/null; then
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

searxng.install.packages() {
    TITLE="SearXNG -- install packages" pkg_install "${SEARXNG_PACKAGES}"
}

searxng.install.buildhost() {
    TITLE="SearXNG -- install buildhost packages" pkg_install \
         "${SEARXNG_PACKAGES} ${SEARXNG_BUILD_PACKAGES}"
}

searxng.install.clone() {
    rst_title "Clone SearXNG sources" section
    if ! service_account_is_available "${SERVICE_USER}"; then
        die 42 "To clone SearXNG, first install user ${SERVICE_USER}."
    fi
    echo
    if ! sudo -i -u "${SERVICE_USER}" ls -d "$REPO_ROOT" > /dev/null; then
        die 42 "user '${SERVICE_USER}' missed read permission: $REPO_ROOT"
    fi
    # SERVICE_HOME="$(sudo -i -u "${SERVICE_USER}" echo \$HOME 2>/dev/null)"
    if [[ ! "${SERVICE_HOME}" ]]; then
        err_msg "to clone SearXNG sources, user ${SERVICE_USER} hast to be created first"
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
    # https://github.com/searxng/searxng/issues/1251
    git_clone "$REPO_ROOT" "${SEARXNG_SRC}" \
              "$GIT_BRANCH" "${SERVICE_USER}"
    git config --system --add safe.directory "${SEARXNG_SRC}"

    pushd "${SEARXNG_SRC}" > /dev/null
    tee_stderr 0.1 <<EOF | sudo -H -u "${SERVICE_USER}" -i 2>&1 | prefix_stdout "$_service_prefix"
cd "${SEARXNG_SRC}"
git remote set-url origin ${GIT_URL}
git config user.email "${ADMIN_EMAIL}"
git config user.name "${ADMIN_NAME}"
git config --list
EOF
    popd > /dev/null
}

searxng.install.link_src() {
    rst_title "link SearXNG's sources to: $2" chapter
    echo
    tee_stderr 0.1 <<EOF | sudo -H -u "${SERVICE_USER}" -i 2>&1 | prefix_stdout "$_service_prefix"
mv -f "${SEARXNG_SRC}" "${SEARXNG_SRC}.backup"
ln -s "${2}" "${SEARXNG_SRC}"
ls -ld /usr/local/searxng/searxng-src
EOF
    echo
    uWSGI_restart "$SEARXNG_UWSGI_APP"
}

searxng.install.pyenv() {
    rst_title "Create virtualenv (python)" section
    echo
    if [[ ! -f "${SEARXNG_SRC}/manage" ]]; then
        die 42 "To create pyenv for SearXNG, first install searxng-src."
    fi
    info_msg "create pyenv in ${SEARXNG_PYENV}"
    tee_stderr 0.1 <<EOF | sudo -H -u "${SERVICE_USER}" -i 2>&1 | prefix_stdout "$_service_prefix"
rm -rf "${SEARXNG_PYENV}"
python3 -m venv "${SEARXNG_PYENV}"
grep -qFs -- 'source ${SEARXNG_PYENV}/bin/activate' ~/.profile \
  || echo 'source ${SEARXNG_PYENV}/bin/activate' >> ~/.profile
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
cd ${SEARXNG_SRC}
pip install -e .
EOF
}

searxng.remove.pyenv() {
    rst_title "Remove virtualenv (python)" section
    if ! ask_yn "Do you really want to drop ${SEARXNG_PYENV} ?"; then
        return
    fi
    info_msg "remove pyenv activation from ~/.profile"
    tee_stderr 0.1 <<EOF | sudo -H -u "${SERVICE_USER}" -i 2>&1 |  prefix_stdout "$_service_prefix"
grep -v 'source ${SEARXNG_PYENV}/bin/activate' ~/.profile > ~/.profile.##
mv ~/.profile.## ~/.profile
EOF
    rm -rf "${SEARXNG_PYENV}"
}

searxng.install.settings() {
    rst_title "install ${SEARXNG_SETTINGS_PATH}" section

    if ! [[ -f "${SEARXNG_SRC}/.git/config" ]]; then
        die "Before install settings, first install SearXNG."
        exit 42
    fi

    mkdir -p "$(dirname "${SEARXNG_SETTINGS_PATH}")"

    DEFAULT_SELECT=1 \
                  install_template --no-eval \
                  "${SEARXNG_SETTINGS_PATH}" \
                  "${SERVICE_USER}" "${SERVICE_GROUP}"

    tee_stderr 0.1 <<EOF | sudo -H -i 2>&1 | prefix_stdout "root"
sed -i -e "s/ultrasecretkey/$(openssl rand -hex 16)/g" "${SEARXNG_SETTINGS_PATH}"
EOF
}

searxng.remove.settings() {
    rst_title "remove ${SEARXNG_SETTINGS_PATH}" section
    if ask_yn "Do you want to delete the SearXNG settings?" Yn; then
        rm -f "${SEARXNG_SETTINGS_PATH}"
    fi
}

searxng.check() {
    rst_title "SearXNG checks" section

    for NAME in "searx" "filtron" "morty"; do
        if service_account_is_available "${NAME}"; then
            err_msg "There exists an old '${NAME}' account from a previous installation."
        else
            info_msg "[OK] (old) account '${NAME}' does not exists"
        fi
    done

    "${SEARXNG_PYENV}/bin/python" "${SEARXNG_SRC}/utils/searxng_check.py"
}

searxng.instance.update() {
    rst_title "Update SearXNG instance"
    rst_para "fetch from $GIT_URL and reset to origin/$GIT_BRANCH"
    tee_stderr 0.3 <<EOF | sudo -H -u "${SERVICE_USER}" -i 2>&1 | prefix_stdout "$_service_prefix"
cd ${SEARXNG_SRC}
git fetch origin "$GIT_BRANCH"
git reset --hard "origin/$GIT_BRANCH"
pip install -U pip
pip install -U setuptools
pip install -U wheel
pip install -U pyyaml
pip install -U -e .
EOF
    rst_para "update instance's settings.yml from ${SEARXNG_SETTINGS_PATH}"
    DEFAULT_SELECT=2 \
                  install_template --no-eval \
                  "${SEARXNG_SETTINGS_PATH}" \
                  "${SERVICE_USER}" "${SERVICE_GROUP}"

    sudo -H -i <<EOF
sed -i -e "s/ultrasecretkey/$(openssl rand -hex 16)/g" "${SEARXNG_SETTINGS_PATH}"
EOF
    uWSGI_restart "${SEARXNG_UWSGI_APP}"
}

searxng.install.uwsgi() {
    rst_title "SearXNG (install uwsgi)"
    install_uwsgi
    if [[ ${SEARXNG_UWSGI_USE_SOCKET} == true ]]; then
        searxng.install.uwsgi.socket
    else
        searxng.install.uwsgi.http
    fi
}

searxng.install.uwsgi.http() {
    rst_para "Install ${SEARXNG_UWSGI_APP} at: http://${SEARXNG_INTERNAL_HTTP}"
    uWSGI_install_app "${SEARXNG_UWSGI_APP}"
    if ! searxng.uwsgi.available; then
        err_msg "URL http://${SEARXNG_INTERNAL_HTTP} not available, check SearXNG & uwsgi setup!"
    fi
}

searxng.install.uwsgi.socket() {
    rst_para "Install ${SEARXNG_UWSGI_APP} using socket at: ${SEARXNG_UWSGI_SOCKET}"
    mkdir -p "$(dirname ${SEARXNG_UWSGI_SOCKET})"
    chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "$(dirname ${SEARXNG_UWSGI_SOCKET})"

    case $DIST_ID-$DIST_VERS in
        fedora-*)
            # Fedora runs uWSGI in emperor-tyrant mode: in Tyrant mode the
            # Emperor will run the vassal using the UID/GID of the vassal
            # configuration file [1] (user and group of the app .ini file).
            # [1] https://uwsgi-docs.readthedocs.io/en/latest/Emperor.html#tyrant-mode-secure-multi-user-hosting
            uWSGI_install_app --variant=socket  "${SEARXNG_UWSGI_APP}" "${SERVICE_USER}" "${SERVICE_GROUP}"
            ;;
        *)
            uWSGI_install_app --variant=socket  "${SEARXNG_UWSGI_APP}"
            ;;
    esac
    sleep 5
    if ! searxng.uwsgi.available; then
        err_msg "uWSGI socket not available at: ${SEARXNG_UWSGI_SOCKET}"
    fi
}

searxng.uwsgi.available() {
    if [[ ${SEARXNG_UWSGI_USE_SOCKET} == true ]]; then
        [[ -S "${SEARXNG_UWSGI_SOCKET}" ]]
        exit_val=$?
        if [[ $exit_val = 0 ]]; then
            info_msg "uWSGI socket is located at: ${SEARXNG_UWSGI_SOCKET}"
        fi
    else
        service_is_available "http://${SEARXNG_INTERNAL_HTTP}"
        exit_val=$?
    fi
    return "$exit_val"
}

searxng.remove.uwsgi() {
    rst_title "Remove SearXNG's uWSGI app (${SEARXNG_UWSGI_APP})" section
    echo
    uWSGI_remove_app "${SEARXNG_UWSGI_APP}"
}

searxng.install.redis() {
    rst_title "SearXNG (install redis)"
    redis.build
    redis.install
    redis.addgrp "${SERVICE_USER}"
}

searxng.remove.redis() {
    rst_title "SearXNG (remove redis)"
    redis.rmgrp "${SERVICE_USER}"
    redis.remove
}

searxng.instance.localtest() {
    rst_title "Test SearXNG instance locally" section
    rst_para "Activate debug mode, start a minimal SearXNG "\
             "service and debug a HTTP request/response cycle."

    if service_is_available "http://${SEARXNG_INTERNAL_HTTP}" &>/dev/null; then
        err_msg "URL/port http://${SEARXNG_INTERNAL_HTTP} is already in use, you"
        err_msg "should stop that service before starting local tests!"
        if ! ask_yn "Continue with local tests?"; then
            return
        fi
    fi
    echo
    searxng.instance.debug.on
    tee_stderr 0.1 <<EOF | sudo -H -u "${SERVICE_USER}" -i 2>&1 |  prefix_stdout "$_service_prefix"
export SEARXNG_SETTINGS_PATH="${SEARXNG_SETTINGS_PATH}"
cd ${SEARXNG_SRC}
timeout 10 python searx/webapp.py &
sleep 3
curl --location --verbose --head --insecure ${SEARXNG_INTERNAL_HTTP}
EOF
    echo
    searxng.instance.debug.off
}

searxng.install.http.pre() {
    if ! searxng.uwsgi.available; then
        rst_para "\
To install uWSGI use::

    $(basename "$0") install uwsgi
"
        die 42 "SearXNG's uWSGI app not available"
    fi

    if ! searxng.instance.exec python -c "from searx.shared import redisdb; redisdb.initialize() or exit(42)"; then
        rst_para "\
The configured redis DB is not available: If your server is public to the
internet, you should setup a bot protection to block excessively bot queries.
Bot protection requires a redis DB.  About bot protection visit the official
SearXNG documentation and query for the word 'limiter'.
"
    fi
}

searxng.apache.install() {
    rst_title "Install Apache site ${APACHE_SEARXNG_SITE}"
    rst_para "\
This installs SearXNG's uWSGI app as apache site.  The apache site is located at:
${APACHE_SITES_AVAILABLE}/${APACHE_SEARXNG_SITE}."
    searxng.install.http.pre

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

    if [[ ${SEARXNG_UWSGI_USE_SOCKET} == true ]]; then
        apache_install_site --variant=socket "${APACHE_SEARXNG_SITE}"
    else
        apache_install_site "${APACHE_SEARXNG_SITE}"
    fi

    if ! service_is_available "${SEARXNG_URL}"; then
        err_msg "Public service at ${SEARXNG_URL} is not available!"
    fi
}

searxng.apache.remove() {
    rst_title "Remove Apache site ${APACHE_SEARXNG_SITE}"
    rst_para "\
This removes apache site ${APACHE_SEARXNG_SITE}::

  ${APACHE_SITES_AVAILABLE}/${APACHE_SEARXNG_SITE}"

    ! apache_is_installed && err_msg "Apache is not installed."
    if ! ask_yn "Do you really want to continue?" Yn; then
        return
    fi
    apache_remove_site "${APACHE_SEARXNG_SITE}"
}

searxng.nginx.install() {

    rst_title "Install nginx site ${NGINX_SEARXNG_SITE}"
    rst_para "\
This installs SearXNG's uWSGI app as Nginx site.  The Nginx site is located at:
${NGINX_APPS_AVAILABLE}/${NGINX_SEARXNG_SITE} and requires a uWSGI."
    searxng.install.http.pre

    if ! nginx_is_installed ; then
        err_msg "Nginx packages are not installed"
        if ! ask_yn "Do you really want to continue and install Nginx packages?" Yn; then
            return
        else
            FORCE_SELECTION=Y install_nginx
        fi
    else
        info_msg "Nginx packages are installed [OK]"
    fi

    if [[ ${SEARXNG_UWSGI_USE_SOCKET} == true ]]; then
        nginx_install_app --variant=socket "${NGINX_SEARXNG_SITE}"
    else
        nginx_install_app "${NGINX_SEARXNG_SITE}"
    fi

    if ! service_is_available "${SEARXNG_URL}"; then
        err_msg "Public service at ${SEARXNG_URL} is not available!"
    fi
}

searxng.nginx.remove() {
    rst_title "Remove Nginx site ${NGINX_SEARXNG_SITE}"
    rst_para "\
This removes Nginx site ${NGINX_SEARXNG_SITE}::

  ${NGINX_APPS_AVAILABLE}/${NGINX_SEARXNG_SITE}"

    ! nginx_is_installed && err_msg "Nginx is not installed."
    if ! ask_yn "Do you really want to continue?" Yn; then
        return
    fi
    nginx_remove_app "${NGINX_SEARXNG_SITE}"
}

searxng.instance.exec() {
    if ! service_account_is_available "${SERVICE_USER}"; then
        die 42 "can't execute: instance does not exist (missed account ${SERVICE_USER})"
    fi
    sudo -H -i -u "${SERVICE_USER}" \
         SEARXNG_UWSGI_USE_SOCKET="${SEARXNG_UWSGI_USE_SOCKET}" \
         "$@"
}

searxng.instance.self.call() {
    # wrapper to call a function in instance's environment
    info_msg "wrapper:  utils/searxng.sh instance _call $*"
    searxng.instance.exec "${SEARXNG_SRC}/utils/searxng.sh" instance _call "$@"
}

searxng.instance.get_setting() {
    searxng.instance.exec python <<EOF
from searx import get_setting
print(get_setting('$1'))
EOF
}

searxng.instance.debug.on() {
    warn_msg "Do not enable debug in a production environment!"
    info_msg "try to enable debug mode ..."
    tee_stderr 0.1 <<EOF | sudo -H -i 2>&1 |  prefix_stdout "$_service_prefix"
cd ${SEARXNG_SRC}
sed -i -e "s/debug: false/debug: true/g" "$SEARXNG_SETTINGS_PATH"
EOF
    uWSGI_restart "$SEARXNG_UWSGI_APP"
}

searxng.instance.debug.off() {
    info_msg "try to disable debug mode ..."
    tee_stderr 0.1 <<EOF | sudo -H -i 2>&1 |  prefix_stdout "$_service_prefix"
cd ${SEARXNG_SRC}
sed -i -e "s/debug: true/debug: false/g" "$SEARXNG_SETTINGS_PATH"
EOF
    uWSGI_restart "$SEARXNG_UWSGI_APP"
}

searxng.instance.inspect() {
    rst_title "Inspect SearXNG instance"
    echo

    searxng.instance.self.call _searxng.instance.inspect

    local _debug_on
    if ask_yn "Enable SearXNG debug mode?"; then
        searxng.instance.debug.on
        _debug_on=1
    fi
    echo

    case $DIST_ID-$DIST_VERS in
        ubuntu-*|debian-*)
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

    echo -e  "// use ${_BCyan}CTRL-C${_creset} to stop monitoring the log"
    read -r -s -n1 -t 5
    echo

    while true;  do
        trap break 2
        case $DIST_ID-$DIST_VERS in
            ubuntu-*|debian-*) tail -f "/var/log/uwsgi/app/${SERVICE_NAME%.*}.log" ;;
            arch-*)  journalctl -f -u "uwsgi@${SERVICE_NAME%.*}" ;;
            fedora-*)  journalctl -f -u uwsgi ;;
        esac
    done

    if [[ $_debug_on == 1 ]]; then
        searxng.instance.debug.off
    fi
    return 0
}

_searxng.instance.inspect() {
    searxng.instance.env

    if in_container; then
        # shellcheck source=utils/lxc-searxng.env
        source "${REPO_ROOT}/utils/lxc-searxng.env"
        lxc_suite_info
    fi

    MSG="${_Green}[${_BCyan}CTRL-C${_Green}] to stop or [${_BCyan}KEY${_Green}] to continue${_creset}"

    if ! searxng.uwsgi.available; then
        err_msg "SearXNG's uWSGI app not available"
        wait_key
    fi
    if ! service_is_available "${SEARXNG_URL}"; then
        err_msg "Public service at ${SEARXNG_URL} is not available!"
        wait_key
    fi
}

searxng.doc.rst() {
    local debian="${SEARXNG_PACKAGES_debian}"
    local arch="${SEARXNG_PACKAGES_arch}"
    local fedora="${SEARXNG_PACKAGES_fedora}"
    local debian_build="${SEARXNG_BUILD_PACKAGES_debian}"
    local arch_build="${SEARXNG_BUILD_PACKAGES_arch}"
    local fedora_build="${SEARXNG_BUILD_PACKAGES_fedora}"
    debian="$(echo "${debian}" | sed 's/.*/          & \\/' | sed '$ s/.$//')"
    arch="$(echo "${arch}"     | sed 's/.*/          & \\/' | sed '$ s/.$//')"
    fedora="$(echo "${fedora}" | sed 's/.*/          & \\/' | sed '$ s/.$//')"
    debian_build="$(echo "${debian_build}" | sed 's/.*/          & \\/' | sed '$ s/.$//')"
    arch_build="$(echo "${arch_build}"     | sed 's/.*/          & \\/' | sed '$ s/.$//')"
    fedora_build="$(echo "${fedora_build}" | sed 's/.*/          & \\/' | sed '$ s/.$//')"

    if [[ ${SEARXNG_UWSGI_USE_SOCKET} == true ]]; then
        uwsgi_variant=':socket'
    else
        uwsgi_variant=':socket'
    fi

    eval "echo \"$(< "${REPO_ROOT}/docs/build-templates/searxng.rst")\""

    # I use ubuntu-20.04 here to demonstrate that versions are also supported,
    # normally debian-* and ubuntu-* are most the same.

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

            local _show_cursor=""  # prevent from prefix_stdout's trailing show-cursor

            echo -e "\n.. START searxng uwsgi-appini $DIST_NAME"
            echo ".. code:: bash"
            echo
            eval "echo \"$(< "${TEMPLATES}/${uWSGI_APPS_AVAILABLE}/${SEARXNG_UWSGI_APP}${uwsgi_variant}")\"" | prefix_stdout "  "
            echo -e "\n.. END searxng uwsgi-appini $DIST_NAME"

            echo -e "\n.. START nginx socket"
            echo ".. code:: nginx"
            echo
            eval "echo \"$(< "${TEMPLATES}/${NGINX_APPS_AVAILABLE}/${NGINX_SEARXNG_SITE}:socket")\"" | prefix_stdout "  "
            echo -e "\n.. END nginx socket"

            echo -e "\n.. START nginx http"
            echo ".. code:: nginx"
            echo
            eval "echo \"$(< "${TEMPLATES}/${NGINX_APPS_AVAILABLE}/${NGINX_SEARXNG_SITE}")\"" | prefix_stdout "  "
            echo -e "\n.. END nginx http"

            echo -e "\n.. START apache socket"
            echo ".. code:: apache"
            echo
            eval "echo \"$(< "${TEMPLATES}/${APACHE_SITES_AVAILABLE}/${APACHE_SEARXNG_SITE}:socket")\"" | prefix_stdout "  "
            echo -e "\n.. END apache socket"

            echo -e "\n.. START apache http"
            echo ".. code:: apache"
            echo
            eval "echo \"$(< "${TEMPLATES}/${APACHE_SITES_AVAILABLE}/${APACHE_SEARXNG_SITE}")\"" | prefix_stdout "  "
            echo -e "\n.. END apache http"
        )
    done

}

# ----------------------------------------------------------------------------
main "$@"
# ----------------------------------------------------------------------------
