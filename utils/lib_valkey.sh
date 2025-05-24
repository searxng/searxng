#!/usr/bin/env bash
# -*- coding: utf-8; mode: sh indent-tabs-mode: nil -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Tools to build and install valkey [1] binaries & packages.
#
# [1] https://valkey.io/download#installation
#
# 1. valkey.devpkg (sudo)
# 2. valkey.build
# 3. valkey.install (sudo)
#
# systemd commands::
#
#    sudo -H systemctl status searxng-valkey
#    sudo -H journalctl -u searxng-valkey
#    sudo -H journalctl --vacuum-size=1M
#
# Test socket connection from client (local user)::
#
#    $ sudo -H ./manage valkey.addgrp "${USER}"
#    # logout & login to get member of group
#    $ groups
#    ... searxng-valkey ...
#    $ source /usr/local/searxng-valkey/.valkey_env
#    $ which valkey-cli
#    /usr/local/searxng-valkey/.local/bin/valkey-cli
#
#    $ valkey-cli -s /usr/local/searxng-valkey/valkey.sock
#    valkey /usr/local/searxng-valkey/valkey.sock> set foo bar
#    OK
#    valkey /usr/local/searxng-valkey/valkey.sock> get foo
#    "bar"
#    [CTRL-D]


# shellcheck disable=SC2091
# shellcheck source=utils/lib.sh
. /dev/null

VALKEY_GIT_URL="https://github.com/valkey/valkey.git"
VALKEY_GIT_TAG="${VALKEY_GIT_TAG:-6.2.6}"

VALKEY_USER="searxng-valkey"
VALKEY_GROUP="searxng-valkey"

VALKEY_HOME="/usr/local/${VALKEY_USER}"
VALKEY_HOME_BIN="${VALKEY_HOME}/.local/bin"
VALKEY_ENV="${VALKEY_HOME}/.valkey_env"

VALKEY_SERVICE_NAME="searxng-valkey"
VALKEY_SYSTEMD_UNIT="${SYSTEMD_UNITS}/${VALKEY_SERVICE_NAME}.service"

# binaries to compile & install
VALKEY_INSTALL_EXE=(valkey-server valkey-benchmark valkey-cli)
# link names of valkey-server binary
VALKEY_LINK_EXE=(valkey-sentinel valkey-check-rdb valkey-check-aof)

VALKEY_CONF="${VALKEY_HOME}/valkey.conf"
VALKEY_CONF_TEMPLATE=$(cat <<EOF
# Note that in order to read the configuration file, Valkey must be
# started with the file path as first argument:
#
# ./valkey-server /path/to/valkey.conf

# bind 127.0.0.1 -::1
protected-mode yes

# Accept connections on the specified port, default is 6379 (IANA #815344).
# If port 0 is specified Valkey will not listen on a TCP socket.
port 0

# Specify the path for the Unix socket that will be used to listen for
# incoming connections.

unixsocket ${VALKEY_HOME}/run/valkey.sock
unixsocketperm 770

# The working directory.
dir ${VALKEY_HOME}/run

# If you run Valkey from upstart or systemd, Valkey can interact with your
# supervision tree.
supervised auto

pidfile ${VALKEY_HOME}/run/valkey.pid

# log to the system logger
syslog-enabled yes
EOF
)

valkey.help(){
    cat <<EOF
valkey.:
  devpkg    : install essential packages to compile valkey
  build     : build valkey binaries at $(valkey._get_dist)
  install   : create user (${VALKEY_USER}) and install systemd service (${VALKEY_SERVICE_NAME})
  remove    : delete user (${VALKEY_USER}) and remove service (${VALKEY_SERVICE_NAME})
  shell     : start bash interpreter from user ${VALKEY_USER}
  src       : clone valkey source code to <path> and checkput ${VALKEY_GIT_TAG}
  useradd   : create user (${VALKEY_USER}) at ${VALKEY_HOME}
  userdel   : delete user (${VALKEY_USER})
  addgrp    : add <user> to group (${VALKEY_USER})
  rmgrp     : remove <user> from group (${VALKEY_USER})
EOF
}

valkey.devpkg() {

    # Uses OS package manager to install the essential packages to build and
    # compile sources

    sudo_or_exit

    case ${DIST_ID} in
        ubuntu|debian)
            pkg_install git build-essential gawk
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

valkey.build() {

    # usage: valkey.build

    rst_title "get valkey sources" section
    valkey.src "${CACHE}/valkey"

    if ! required_commands gcc nm make gawk ; then
        info_msg "install development tools to get missing command(s) .."
        if [[ -n ${SUDO_USER} ]]; then
            sudo -H "$0" valkey.devpkg
        else
            valkey.devpkg
        fi
    fi

    rst_title "compile valkey sources" section

    pushd "${CACHE}/valkey" &>/dev/null

    if ask_yn "Do you run 'make distclean' first'?" Yn; then
        $(bash.cmd) -c "make distclean" 2>&1 | prefix_stdout
    fi

    $(bash.cmd) -c "make" 2>&1 | prefix_stdout
    if ask_yn "Do you run 'make test'?" Ny; then
        $(bash.cmd) -c "make test" | prefix_stdout
    fi

    popd &>/dev/null

    tee_stderr 0.1 <<EOF | $(bash.cmd) 2>&1 | prefix_stdout
mkdir -p "$(valkey._get_dist)"
cd "${CACHE}/valkey/src"
cp ${VALKEY_INSTALL_EXE[@]} "$(valkey._get_dist)"
EOF
    info_msg "valkey binaries available at $(valkey._get_dist)"
}


valkey.install() {
    sudo_or_exit
    (
        set -e
        valkey.useradd
        valkey._install_bin
        valkey._install_conf
        valkey._install_service
    )
    dump_return $?
}

valkey.remove() {
    sudo_or_exit
    (
        set -e
        valkey._remove_service
        valkey.userdel
    )
    dump_return $?
}

valkey.shell() {
    interactive_shell "${VALKEY_USER}"
}

valkey.src() {

    # usage: valkey.src "${CACHE}/valkey"

    local dest="${1:-${CACHE}/valkey}"

    if [ -d "${dest}" ] ; then
        info_msg "already cloned: $dest"
        tee_stderr 0.1 <<EOF | $(bash.cmd) 2>&1 | prefix_stdout
cd "${dest}"
git fetch --all
git reset --hard tags/${VALKEY_GIT_TAG}
EOF
    else
        tee_stderr 0.1 <<EOF | $(bash.cmd) 2>&1 | prefix_stdout
mkdir -p "$(dirname "$dest")"
cd "$(dirname "$dest")"
git clone "${VALKEY_GIT_URL}" "${dest}"
EOF
        tee_stderr 0.1 <<EOF | $(bash.cmd) 2>&1 | prefix_stdout
cd "${dest}"
git checkout tags/${VALKEY_GIT_TAG} -b "build-branch"
EOF
    fi
}

valkey.useradd(){

    # usage: valkey.useradd

    rst_title "add user ${VALKEY_USER}" section
    echo
    sudo_or_exit

    # create user account
    tee_stderr 0.5 <<EOF | sudo -H bash | prefix_stdout
useradd --shell /bin/bash --system \
 --home-dir "${VALKEY_HOME}" \
 --comment 'user that runs a valkey instance' "${VALKEY_USER}"
mkdir -p "${VALKEY_HOME}"
chown -R "${VALKEY_USER}:${VALKEY_GROUP}" "${VALKEY_HOME}"
groups "${VALKEY_USER}"
EOF

    # create App-ENV and add source it in the .profile
    tee_stderr 0.5 <<EOF | sudo -H -u "${VALKEY_USER}" bash | prefix_stdout
mkdir -p "${VALKEY_HOME_BIN}"
echo "export PATH=${VALKEY_HOME_BIN}:\\\$PATH" > "${VALKEY_ENV}"
grep -qFs -- 'source "${VALKEY_ENV}"' ~/.profile || echo 'source "${VALKEY_ENV}"' >> ~/.profile
EOF
}

valkey.userdel() {
    sudo_or_exit
    drop_service_account "${VALKEY_USER}"
    groupdel "${VALKEY_GROUP}" 2>&1 | prefix_stdout || true
}

valkey.addgrp() {

    # usage: valkey.addgrp <user>

    [[ -z $1 ]] && die_caller 42 "missing argument <user>"
    sudo -H gpasswd -a "$1" "${VALKEY_GROUP}"
}

valkey.rmgrp() {

    # usage: valkey.rmgrp <user>

    [[ -z $1 ]] && die_caller 42 "missing argument <user>"
    sudo -H gpasswd -d "$1" "${VALKEY_GROUP}"

}


# private valkey. functions
# ------------------------

valkey._install_bin() {
    local src
    src="$(valkey._get_dist)"
    (
        set -e
        for valkey_exe in "${VALKEY_INSTALL_EXE[@]}"; do
            install -v -o "${VALKEY_USER}" -g "${VALKEY_GROUP}" \
                 "${src}/${valkey_exe}" "${VALKEY_HOME_BIN}"
        done

        pushd "${VALKEY_HOME_BIN}" &> /dev/null
        for valkey_exe in "${VALKEY_LINK_EXE[@]}"; do
            info_msg "link valkey-server --> ${valkey_exe}"
            sudo -H -u "${VALKEY_USER}" ln -sf valkey-server "${valkey_exe}"
        done
        popd &> /dev/null

    )
}

valkey._install_conf() {
        sudo -H -u "${VALKEY_USER}" bash <<EOF
mkdir -p "${VALKEY_HOME}/run"
echo '${VALKEY_CONF_TEMPLATE}' > "${VALKEY_CONF}"
EOF
}

valkey._install_service() {
    systemd_install_service "${VALKEY_SERVICE_NAME}" "${VALKEY_SYSTEMD_UNIT}"
}

valkey._remove_service() {
    systemd_remove_service "${VALKEY_SERVICE_NAME}" "${VALKEY_SYSTEMD_UNIT}"
}

valkey._get_dist() {
    if [ -z "${VALKEY_DIST}" ]; then
        echo "${REPO_ROOT}/dist/valkey/${VALKEY_GIT_TAG}/$(valkey._arch)"
    else
        echo "${VALKEY_DIST}"
    fi
}

valkey._arch() {
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
