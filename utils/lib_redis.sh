#!/usr/bin/env bash
# -*- coding: utf-8; mode: sh indent-tabs-mode: nil -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Tools to build and install redis [1] binaries & packages.
#
# [1] https://redis.io/download#installation
#
# 1. redis.devpkg (sudo)
# 2. redis.build
# 3. redis.install (sudo)
#
# systemd commands::
#
#    sudo -H systemctl status searxng-redis
#    sudo -H journalctl -u searxng-redis
#    sudo -H journalctl --vacuum-size=1M
#
# Test socket connection from client (local user)::
#
#    $ sudo -H ./manage redis.addgrp "${USER}"
#    # logout & login to get member of group
#    $ groups
#    ... searxng-redis ...
#    $ source /usr/local/searxng-redis/.redis_env
#    $ which redis-cli
#    /usr/local/searxng-redis/.local/bin/redis-cli
#
#    $ redis-cli -s /usr/local/searxng-redis/redis.sock
#    redis /usr/local/searxng-redis/redis.sock> set foo bar
#    OK
#    redis /usr/local/searxng-redis/redis.sock> get foo
#    "bar"
#    [CTRL-D]


# shellcheck disable=SC2091
# shellcheck source=utils/lib.sh
. /dev/null

REDIS_GIT_URL="https://github.com/redis/redis.git"
REDIS_GIT_TAG="${REDIS_GIT_TAG:-6.2.6}"

REDIS_USER="searxng-redis"
REDIS_HOME="/usr/local/${REDIS_USER}"
REDIS_HOME_BIN="${REDIS_HOME}/.local/bin"
REDIS_ENV="${REDIS_HOME}/.redis_env"

REDIS_SERVICE_NAME="searxng-redis"
REDIS_SYSTEMD_UNIT="${SYSTEMD_UNITS}/${REDIS_SERVICE_NAME}.service"

# binaries to compile & install
REDIS_INSTALL_EXE=(redis-server redis-benchmark redis-cli)
# link names of redis-server binary
REDIS_LINK_EXE=(redis-sentinel redis-check-rdb redis-check-aof)

REDIS_CONF="${REDIS_HOME}/redis.conf"
REDIS_CONF_TEMPLATE=$(cat <<EOF
# Note that in order to read the configuration file, Redis must be
# started with the file path as first argument:
#
# ./redis-server /path/to/redis.conf

# bind 127.0.0.1 -::1
protected-mode yes

# Accept connections on the specified port, default is 6379 (IANA #815344).
# If port 0 is specified Redis will not listen on a TCP socket.
port 0

# Specify the path for the Unix socket that will be used to listen for
# incoming connections.

unixsocket ${REDIS_HOME}/run/redis.sock
unixsocketperm 770

# The working directory.
dir ${REDIS_HOME}/run

# If you run Redis from upstart or systemd, Redis can interact with your
# supervision tree.
supervised auto

pidfile ${REDIS_HOME}/run/redis.pid

# log to the system logger
syslog-enabled yes
EOF
)

redis.help(){
    cat <<EOF
redis.:
  devpkg    : install essential packages to compile redis
  build     : build redis binaries at $(redis._get_dist)
  install   : create user (${REDIS_USER}) and install systemd service (${REDIS_SERVICE_NAME})
  remove    : delete user (${REDIS_USER}) and remove service (${REDIS_SERVICE_NAME})
  shell     : start bash interpreter from user ${REDIS_USER}
  src       : clone redis source code to <path> and checkput ${REDIS_GIT_TAG}
  useradd   : create user (${REDIS_USER}) at ${REDIS_HOME}
  userdel   : delete user (${REDIS_USER})
  addgrp    : add <user> to group (${REDIS_USER})
  rmgrp     : remove <user> from group (${REDIS_USER})
EOF
}

redis.devpkg() {

    # Uses OS package manager to install the essential packages to build and
    # compile sources

    sudo_or_exit

    case ${DIST_ID} in
        ubuntu|debian)
            pkg_install git build-essential
            ;;
        arch)
            pkg_install git base-devel
            ;;
        fedora)
            pkg_install git @development-tools
            ;;
        centos)
            pkg_install git
            yum groupinstall "Development Tools" -y
            ;;
        *)
            err_msg "$DIST_ID-$DIST_VERS: No rules to install development tools from OS."
            return 42
            ;;
    esac
}

redis.build() {

    # usage: redis.build

    rst_title "get redis sources" section
    redis.src "${CACHE}/redis"

    if ! required_commands gcc nm make gawk; then
        sudo -H "$0" redis.devpkg
    fi

    rst_title "compile redis sources" section

    pushd "${CACHE}/redis" &>/dev/null

    if ask_yn "Do you run 'make distclean' first'?" Ny; then
        $(bash.cmd) -c "make distclean" 2>&1 | prefix_stdout
    fi

    $(bash.cmd) -c "make" 2>&1 | prefix_stdout
    if ask_yn "Do you run 'make test'?" Ny; then
        $(bash.cmd) -c "make test" | prefix_stdout
    fi

    popd &>/dev/null

    tee_stderr 0.1 <<EOF | $(bash.cmd) 2>&1 |  prefix_stdout
mkdir -p "$(redis._get_dist)"
cd "${CACHE}/redis/src"
cp ${REDIS_INSTALL_EXE[@]} "$(redis._get_dist)"
EOF
    info_msg "redis binaries available at $(redis._get_dist)"
}


redis.install() {
    sudo_or_exit
    (
        set -e
        redis.useradd
        redis._install_bin
        redis._install_conf
        redis._install_service
    )
    dump_return $?
}

redis.remove() {
    sudo_or_exit
    (
        set -e
        redis._remove_service
        redis.userdel
    )
    dump_return $?
}

redis.shell() {
    interactive_shell "${REDIS_USER}"
}

redis.src() {

    # usage: redis.src "${CACHE}/redis"

    local dest="${1:-${CACHE}/redis}"

    if [ -d "${dest}" ] ; then
        info_msg "already cloned: $dest"
        tee_stderr 0.1 <<EOF | $(bash.cmd) 2>&1 | prefix_stdout
cd "${dest}"
git fetch --all
git reset --hard tags/${REDIS_GIT_TAG}
EOF
    else
        tee_stderr 0.1 <<EOF | $(bash.cmd) 2>&1 | prefix_stdout
mkdir -p "$(dirname "$dest")"
cd "$(dirname "$dest")"
git clone "${REDIS_GIT_URL}" "${dest}"
EOF
        tee_stderr 0.1 <<EOF | $(bash.cmd) 2>&1 | prefix_stdout
cd "${dest}"
git checkout tags/${REDIS_GIT_TAG} -b "build-branch"
EOF
    fi
}

redis.useradd(){

    # usage: redis.useradd

    rst_title "add user ${REDIS_USER}" section
    echo
    sudo_or_exit

    # create user account
    tee_stderr 0.5 <<EOF | sudo -H bash | prefix_stdout
useradd --shell /bin/bash --system \
 --home-dir "${REDIS_HOME}" \
 --comment 'user that runs a redis instance' "${REDIS_USER}"
mkdir -p "${REDIS_HOME}"
chown -R "${REDIS_USER}:${REDIS_USER}" "${REDIS_HOME}"
groups "${REDIS_USER}"
EOF

    # create App-ENV and add source it in the .profile
    tee_stderr 0.5 <<EOF | sudo -H -u "${REDIS_USER}" bash | prefix_stdout
mkdir -p "${REDIS_HOME_BIN}"
echo "export PATH=${REDIS_HOME_BIN}:\\\$PATH" > "${REDIS_ENV}"
grep -qFs -- 'source "${REDIS_ENV}"' ~/.profile || echo 'source "${REDIS_ENV}"' >> ~/.profile
EOF
}

redis.userdel() {
    sudo_or_exit
    drop_service_account "${REDIS_USER}"
    groupdel "${REDIS_USER}" 2>&1 | prefix_stdout || true
}

redis.addgrp() {

    # usage: redis.addgrp <user>

    [[ -z $1 ]] && die_caller 42 "missing argument <user>"
    sudo -H gpasswd -a "$1" "${REDIS_USER}"
}

redis.rmgrp() {

    # usage: redis.rmgrp <user>

    [[ -z $1 ]] && die_caller 42 "missing argument <user>"
    sudo -H gpasswd -d "$1" "${REDIS_USER}"

}


# private redis. functions
# ------------------------

redis._install_bin() {
    local src
    src="$(redis._get_dist)"
    (
        set -e
        for redis_exe in "${REDIS_INSTALL_EXE[@]}"; do
            install -v -o "${REDIS_USER}" -g "${REDIS_USER}" \
                 "${src}/${redis_exe}" "${REDIS_HOME_BIN}"
        done

        pushd "${REDIS_HOME_BIN}" &> /dev/null
        for redis_exe in "${REDIS_LINK_EXE[@]}"; do
            info_msg "link redis-server --> ${redis_exe}"
            sudo -H -u "${REDIS_USER}" ln -sf redis-server "${redis_exe}"
        done
        popd &> /dev/null

    )
}

redis._install_conf() {
        sudo -H -u "${REDIS_USER}" bash <<EOF
mkdir -p "${REDIS_HOME}/run"
echo '${REDIS_CONF_TEMPLATE}' > "${REDIS_CONF}"
EOF
}

redis._install_service() {
    systemd_install_service "${REDIS_SERVICE_NAME}" "${REDIS_SYSTEMD_UNIT}"
}

redis._remove_service() {
    systemd_remove_service "${REDIS_SERVICE_NAME}" "${REDIS_SYSTEMD_UNIT}"
}

redis._get_dist() {
    if [ -z "${REDIS_DIST}" ]; then
        echo "${REPO_ROOT}/dist/redis/${REDIS_GIT_TAG}/$(redis._arch)"
    else
        echo "${REDIS_DIST}"
    fi
}

redis._arch() {
    local ARCH
    case "$(command uname -m)" in
        "x86_64") ARCH=amd64 ;;
        "aarch64") ARCH=arm64 ;;
        "armv6" | "armv7l") ARCH=armv6l ;;
        "armv8") ARCH=arm64 ;;
        .*386.*) ARCH=386 ;;
        ppc64*) ARCH=ppc64le ;;
    *)  die 42 "ARCH is unknown: $(command uname -m)" ;;
    esac
    echo "${ARCH}"
}

# TODO: move this to the right place ..

bash.cmd(){

    # print cmd to get a bash in a non-root mode, even if we are in a sudo
    # context.

    local user="${USER}"
    local bash_cmd="bash"

    if [ -n "${SUDO_USER}" ] && [ "root" != "${SUDO_USER}" ] ; then
        user="${SUDO_USER}"
        bash_cmd="sudo -H -u ${SUDO_USER} bash"
    fi

    printf "%s" "${bash_cmd}"
}
