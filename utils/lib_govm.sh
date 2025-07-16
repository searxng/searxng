#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Go versions manager to install and maintain golang [1] binaries & packages.
#
# [1] https://golang.org/doc/devel/release#policy

# shellcheck source=utils/lib.sh
. /dev/null

# configure golang environment for go.vm
# --------------------------------------

_GO_DL_URL="https://go.dev/dl"

GOVERSION="${GOVERSION:-go$(awk '/^go /{print $2}' "${REPO_ROOT}/go.mod")}"
GOTOOLCHAIN=local

GOROOT="${REPO_ROOT}/.govm/${GOVERSION}"
GOENV="${GOROOT}/.config/go.env"
GOVM_EXE="${GOROOT}/bin/go"

GOPATH="${REPO_ROOT}/local/${GOVERSION}" # no support for multiple path names!!
GOCACHE="${GOPATH}/.cache/go-build"
GOMODCACHE="${GOPATH}/pkg/mod"

# implement go functions
# -----------------------

go.help() {
    cat <<EOF
go:           GOROOT=${GOROOT}
  install   : compiles and installs packages
EOF
}

go.tool() {
    # shortcut for "go tool .." in the Go environment
    go.env.dev
    "${GOVM_EXE}" tool "$@"
}

go.env.dev() {
    if [ -z "$_GO_DEVTOOLS_INSTALLED" ]; then
        build_msg INSTALL "[pkg.go.dev] ./go.mod: developer and CI tools"
        go.tidy
    else
        go.vm.ensure
        _GO_DEVTOOLS_INSTALLED=1
    fi
}

go.tidy() {
    go.vm.ensure
    "${GOVM_EXE}" mod tidy
    chmod -R u+w "${GOMODCACHE}"
}

go.clean() {
    if ! go.vm.is_installed; then
        build_msg CLEAN "[Go] not installed"
        return 0
    fi
    build_msg CLEAN "[Go] drop folders ${GOROOT} and ${GOPATH}"
    rm -rf "${GOROOT}" "${GOPATH}"
}

go.install() {
    go.vm.ensure
    GOENV="${GOENV}" "${GOVM_EXE}" install "$@"
    # not sure why, but go installs some files without setting the write access
    # for the file owner
    chmod -R u+w "${GOMODCACHE}"
}

go.os() {
    local OS
    case "$(command uname -a)xx" in
        Linux\ *) OS=linux ;;
        Darwin\ *) OS=darwin ;;
        FreeBSD\ *) OS=freebsd ;;
        CYGWIN* | MSYS* | MINGW*) OS=windows ;;
        *) die 42 "OS is unknown: $(command uname -a)" ;;
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
        *) die 42 "ARCH is unknown: $(command uname -m)" ;;
    esac
    echo "${ARCH}"
}

# Go version management (go.vm)
# -----------------------------

go.vm.ensure() {
    if ! go.vm.is_installed; then
        # shellcheck disable=SC2119
        go.vm.install
    fi
}

go.vm.is_installed() {
    # is true if "go" command is installed
    [[ -f "${GOROOT}/bin/go" ]]
}

# shellcheck disable=SC2120
go.vm.install() {

    # Go versions manager; to install Go at arbitrary place:
    #
    # usage:  go.vm.install <version> <dest>

    local version dest fname sha size tmp
    version="${1:-$GOVERSION}"
    dest="${2:-$GOROOT}"

    info_msg "Install Go in ${dest}"

    # HINT: the python requirements needed by go.vm.version are taken from the
    # developer environment. If it is not yet installed, install it now ..
    pyenv.install

    # fetch go version ..
    local buf=()
    mapfile -t buf < <(
        go.vm.version "${version}" archive "$(go.os)" "$(go.arch)" filename sha256 size
    )
    if [ ${#buf[@]} -eq 0 ]; then
        die 42 "can't find info of golang version: ${version}"
    fi
    fname="${buf[0]}"
    sha="${buf[1]}"
    size="$(numfmt --to=iec "${buf[2]}")"

    info_msg "Download go binary ${fname} (${size}B)"
    cache_download "${_GO_DL_URL}/${fname}" "${fname}"

    pushd "${CACHE}" &>/dev/null
    echo "${sha}  ${fname}" >"${fname}.sha256"
    if ! sha256sum -c "${fname}.sha256" >/dev/null; then
        die 42 "downloaded file ${fname} checksum does not match"
    else
        info_msg "${fname} checksum OK"
    fi
    popd &>/dev/null

    info_msg "install golang"

    tmp="$(mktemp -d)"
    tar -C "${tmp}" -xzf "${CACHE}/${fname}"
    rm -rf "${dest}"
    mkdir -p "$(dirname "${dest}")"
    mv "${tmp}/go" "${dest}"

    mkdir -p "$(dirname "$GOENV")"
    export GOENV

    "${GOVM_EXE}" telemetry off
    "${GOVM_EXE}" env -w \
        GOBIN="$GOBIN" \
        GOTOOLCHAIN="$GOTOOLCHAIN" \
        GOCACHE="$GOCACHE" \
        GOPATH="$GOPATH" \
        GOMODCACHE="$GOMODCACHE"

    mkdir -p "${GOMODCACHE}"
}

go.vm.list() {

    # Go versions manager; list Go versions (stable)

    "${PY_ENV_BIN}/python" <<EOF
import sys, json, requests
resp = requests.get("${_GO_DL_URL}/?mode=json&include=all")
for ver in json.loads(resp.text):
    if not ver['stable']:
        continue
    for f in ver['files']:
        if f['kind'] != 'archive' or not f['size'] or not f['sha256'] or len(f['os']) < 2:
            continue
        print(" %(version)-10s|%(os)-8s|%(arch)-8s|%(filename)-30s|%(size)-10s|%(sha256)s" % f)
EOF
}

go.vm.version() {

    # Print information about a Go distribution. To print filename sha256 and
    # size of the archive that fits to your OS and host:
    #
    #   go.ver_info "${GOVERSION}" archive "$(go.os)" "$(go.arch)" filename sha256 size
    #
    # usage: go.vm.version <go-vers> <kind> <os> <arch> [filename|sha256|size]
    #
    # kind:  [archive|source|installer]
    # os:    [darwin|freebsd|linux|windows]
    # arch:  [amd64|arm64|386|armv6l|ppc64le|s390x]

    "${PY_ENV_BIN}/python" - "$@" <<EOF
import sys, json, requests
resp = requests.get("${_GO_DL_URL}/?mode=json&include=all")
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
