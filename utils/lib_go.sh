#!/usr/bin/env bash
# -*- coding: utf-8; mode: sh indent-tabs-mode: nil -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Tools to install and maintain golang [1] binaries & packages.
#
# [1] https://golang.org/doc/devel/release#policy
#
# A simple *helloworld* test with user 'my_user' :
#
#   sudo -H adduser my_user
#   ./manage go.golang go1.17.3 my_user
#   ./manage go.install github.com/go-training/helloworld@latest my_user
#   ./manage go.bash my_user
#   $ helloword
#   Hello World!!
#
# Don't forget to remove 'my_user':  sudo -H deluser --remove-home my_user

# shellcheck source=utils/lib.sh
. /dev/null

# shellcheck disable=SC2034
declare main_cmd

# configure golang environment
# ----------------------------

[[ -z "${GO_VERSION}" ]] && GO_VERSION="go1.17.3"

GO_DL_URL="https://golang.org/dl"

# implement go functions
# -----------------------

go.help(){
    cat <<EOF
go.:
  ls        : list golang binary archives (stable)
  golang    : (re-) install golang binary in user's \$HOME/local folder
  install   : install go package in user's \$HOME/go-apps folder
  bash      : start bash interpreter with golang environment sourced
EOF
}

go.ls(){
    python3 <<EOF
import sys, json, requests
resp = requests.get("${GO_DL_URL}/?mode=json&include=all")
for ver in json.loads(resp.text):
    if not ver['stable']:
        continue
    for f in ver['files']:
        if f['kind'] != 'archive' or not f['size'] or not f['sha256'] or len(f['os']) < 2:
            continue
        print(" %(version)-10s|%(os)-8s|%(arch)-8s|%(filename)-30s|%(size)-10s|%(sha256)s" % f)
EOF
}

go.ver_info(){

    # print informations about a golang distribution. To print filename
    # sha256 and size of the archive that fits to your OS and host:
    #
    #   go.ver_info "${GO_VERSION}" archive "$(go.os)" "$(go.arch)" filename sha256 size
    #
    # usage: go.ver_info <go-vers> <kind> <os> <arch> [filename|sha256|size]
    #
    # kind:  [archive|source|installer]
    # os:    [darwin|freebsd|linux|windows]
    # arch:  [amd64|arm64|386|armv6l|ppc64le|s390x]

    python3 - "$@" <<EOF
import sys, json, requests
resp = requests.get("${GO_DL_URL}/?mode=json&include=all")
for ver in json.loads(resp.text):
    if ver['version'] != sys.argv[1]:
        continue
    for f in ver['files']:
        if (f['kind'] != sys.argv[2] or f['os'] != sys.argv[3] or f['arch'] != sys.argv[4]):
            continue
        for x in sys.argv[5:]:
           print(f[x])
        sys.exit(0)
sys.exit(42)
EOF
}

go.os() {
  local OS
  case "$(command uname -a)xx" in
    Linux\ *) OS=linux ;;
    Darwin\ *) OS=darwin ;;
    FreeBSD\ *) OS=freebsd ;;
    CYGWIN* | MSYS* | MINGW*) OS=windows ;;
    *)  die 42 "OS is unknown: $(command uname -a)" ;;
  esac
  echo "${OS}"
}

go.arch() {
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

go.golang() {

    # install golang binary in user's $HOME/local folder:
    #
    #   go.golang ${GO_VERSION} ${SERVICE_USER}
    #
    # usage:  go.golang <go-vers> [<username>]

    local version fname sha size user userpr
    local buf=()

    version="${1:-${GO_VERSION}}"
    user="${2:-${USERNAME}}"
    userpr="  ${_Yellow}|${user}|${_creset} "

    rst_title "Install Go in ${user}'s HOME" section

    mapfile -t buf < <(
        go.ver_info "${version}" archive "$(go.os)" "$(go.arch)" filename sha256 size
    )

    if [ ${#buf[@]} -eq 0 ]; then
        die 42 "can't find info of golang version: ${version}"
    fi
    fname="${buf[0]}"
    sha="${buf[1]}"
    size="$(numfmt --to=iec "${buf[2]}")"

    info_msg "Download go binary ${fname} (${size}B)"
    cache_download "${GO_DL_URL}/${fname}" "${fname}"

    pushd "${CACHE}" &> /dev/null
    echo "${sha}  ${fname}" > "${fname}.sha256"
    if ! sha256sum -c "${fname}.sha256" >/dev/null; then
        die 42 "downloaded file ${fname} checksum does not match"
    else
        info_msg "${fname} checksum OK"
    fi
    popd &> /dev/null

    info_msg "install golang"
    tee_stderr 0.1 <<EOF | sudo -i -u "${user}" | prefix_stdout "${userpr}"
mkdir -p \$HOME/local
rm -rf \$HOME/local/go
tar -C \$HOME/local -xzf ${CACHE}/${fname}
echo "export GOPATH=\$HOME/go-apps" > \$HOME/.go_env
echo "export PATH=\$HOME/local/go/bin:\\\$GOPATH/bin:\\\$PATH" >> \$HOME/.go_env
EOF
    info_msg "test golang installation"
    sudo -i -u "${user}" <<EOF
source \$HOME/.go_env
command -v go
go version
EOF
}

go.install() {

    # install go package in user's $HOME/go-apps folder:
    #
    #   go.install github.com/go-training/helloworld@lates ${SERVICE_USER}
    #
    # usage:  go.install <package> [<username>]

    local package user userpr

    package="${1}"
    user="${2:-${USERNAME}}"
    userpr="  ${_Yellow}|${user}|${_creset} "

    if [ -z "${package}" ]; then
        die 42 "${FUNCNAME[0]}() - missing argument: <package>"
    fi
    tee_stderr 0.1 <<EOF | sudo -i -u "${user}" | prefix_stdout "${userpr}"
source \$HOME/.go_env
go install -v ${package}
EOF
}

go.bash() {

    # start bash interpreter with golang environment sourced
    #
    #   go.bash ${SERVICE_USER}
    #
    # usage:  go.bash [<username>]

    local user
    user="${1:-${USERNAME}}"
    sudo -i -u "${user}" bash --init-file "~${user}/.go_env"
}

go.version(){
    local user
    user="${1:-${USERNAME}}"
    sudo -i -u "${user}" <<EOF
source \$HOME/.go_env
go version | cut -d' ' -f 3
EOF
}
